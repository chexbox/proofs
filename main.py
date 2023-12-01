import os
from wand.image import Image
from wand.color import Color
from wand.drawing import Drawing

SOURCE_DIR = "./source/"
DEST_DIR = "./dest/"

LONG_EDGE = 1000
MARGIN = LONG_EDGE // 12
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_COUNT = 4

files = os.listdir(SOURCE_DIR)

print(len(files), files)

for img_path in files:
    with Image(filename=SOURCE_DIR + img_path) as img:
        # rotate image upright
        try:
            rotate = img.metadata["exif:Orientation"]
            angle = {"6": 90, "8": -90, "3": 180, "5": 90, "7": -90, "4": 180 }.get(rotate[0], 0)
            flip = rotate in ["2", "4", "5", "7"]
            
            if flip:
                img.flop()
                
            img.rotate(angle)
            angle = 0
            
        except:
            print("can't rotate")
            angle = 0
            
        # read camera information
        #print(list(img.metadata))
        
        iso = 0
        
        if "exif:PhotographicSensitivity" in img.metadata:
            iso = int("".join(filter(lambda i:i.isnumeric(), img.metadata["exif:PhotographicSensitivity"].split(" ")[0])))
        
        dpi = 300 if iso < 1200 else 400
            
        desc_list = [img_path]
        
        desc_list.append("(%dx%d): %.1f\" x %.1f\" @ %d dpi" % (img.width, img.height, img.width / dpi, img.height / dpi, dpi))

        #if iso > 0:
        #    desc_list.append("ISO: %d" % iso)

        # if it's portrait, put the samples on the right
        if img.height > img.width:
            img.rotate(90)
            angle -= 90
        
        # generate size and quantity for preview and samples
        scale = max(img.width, img.height) // LONG_EDGE + 1
        
        scaled_width, scaled_height = img.width // scale, img.height // scale
        
        sample_count = min(MAX_SAMPLE_COUNT, (scaled_width + MARGIN) // (min(MIN_SAMPLE_SIZE, scaled_width) + MARGIN))
        sample_size = (scaled_width + MARGIN) // sample_count - MARGIN
        
        print("%20s\tscale: 1/%d (%d %d)\t samples: %d (%d)" % (img_path, scale, scaled_width, scaled_height, sample_count, sample_size))
        
        with Image(width=scaled_width + 2 * MARGIN, height=scaled_height + 3 * MARGIN + sample_size, background=Color('white')) as proof:
            with img.clone() as small_img:
                # scale, if needed
                if scale > 1:
                    small_img.resize(scaled_width, scaled_height)
                
                # add the watermark
                if os.path.exists("watermark.png"):
                    with Image(filename='watermark.png') as watermark:
                        small_img.composite(watermark, left=(small_img.width - watermark.width) // 2, top=small_img.height - watermark.height, operator='over')
                
                proof.composite(small_img, left=MARGIN, top=MARGIN, operator='over')
            
            # select samples from original image
            for sample in range(sample_count):
                with img.clone() as sample_img:
                    # center samples on rule of thirds
                    sample_x = max(0, (sample // 2 % 2 + 1) * img.width // 3 - sample_size // 2)
                    sample_y = max(0, ((sample + 1) // 2 % 2 + 1) * img.height // 3 - sample_size // 2)
                    
                    sample_img.crop(left=sample_x, top=sample_y, width=sample_size, height=sample_size)
                    
                    proof.composite(sample_img, left=MARGIN + sample * (MARGIN + sample_size), top=2 * MARGIN + scaled_height, operator='over')
                
            proof.rotate(angle)
            
            with Drawing() as draw:
                draw.font = "RobotoSlab-Regular.ttf"
                draw.font_size = max(MARGIN // 3, 12)
                draw.text(MARGIN // 2, proof.height - MARGIN // 3, '; '.join(desc_list))
                draw(proof)
                               
            proof.save(filename=DEST_DIR + "proof_" + img_path)
        
            
            