# Hergotzer's Stable Diffusion Regularization image generator

One of the many regularization methods used in Stable Diffusion training, be it full model training or Lora training, are the regularization images. Most often, they are recommended to be generated from the captions of the training set, using the same checkpoint as will be used in the training as well as the same seed, CLIP skip, dimensions and so on. I found this to be extremely annoying to do manually, and couldn't find any scripts or programs for it on the internet (Although they might exist and I just couldn't find them).

So, I made one myself. I really need to note that while I understand some basics of programming, I don't have that much experience with scripting, not even on Python, so I had to ask ChatGPT for help.

I know. 

But, seeing how the final script works really well, is simple to use and requires no dependencies beyond Python and Automatic1111's WEBUI (Which the script uses to actually generate the images), I thought other people might be interested in using it as well, so here it is.

If you want to make any changes to it, be free to. If you want to change some of the generation parameters beyond what the script asks for input, go into the script and look for "payload", and edit what you need. There's a lot of parameters not set by the payload of this script so you'll need to look into A1111's API documentation if you want to add some. 

---

# Requirements

- Python 3.6 or later
- [Automatic1111's WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)

---

# Installation

1. Make sure you have Python 3.6 or later installed
2. Make sure you have Automatic1111's WEBUI installed
3. Place generator_v2.py wherever you want. 

---

# How to Use

1. Start Automatic1111's WEBUI with the --api argument. You can do this by adding --api after COMMANDLINE_ARGS= in the .bat file you use to start the WEBUI. The WEBUI is ready once it prints out the URL it's running on in its console.
2. Run the script: Run the script in your Python environment, be it through command console, a batch file or by simply double-clicking on the script (if your system allows for it).
3. Give the inputs: The script will ask the user for some inputs: The URL the WEBUI is running on, the model/checkpoint to use for generating the images, the training set directory, the dimensions of the images to be generated, the seed or seeds on which generate them and the CLIP skip to use during generation. WARNING: The script will start making calls to the WEBUI API immediately after the last input (CLIP Skips) is given, so make sure the WEBUI is running before that!
4. As the script generates the images, it will save them into a folder in the same directory as the script, called "Results". The folder will be automatically created if not already present. The script generates the images in batches, one folder at a time. I know that the WEBUI has some limitations on how many images can be generated in a single batch, but I am not sure how they work, so I have always just limited the number of images per folder to 100 just to be sure. You can try generating more by having there be more images in the folders, but the WEBUI might start complaining at some point. The script will also give progress updates in its console throughout the process, including an estimated time left.
5. Once all images have been generated, the script will notify the user on the console. All the generated images will be found in the Results -folder in their respective sub-folders, with the same filenames as their respective training images they were derived from.

---

# Notes

- The script expects the training images and their captions to use filenames in the NAME-N -format, where NAME is the concept of the folder (And all training files in the folder have the same NAME) followed by N, the order number. So the contents of one folder could be like [car-1.png, car-1.txt, car-2.png, car-2.txt, car-3.png, car-3.txt...] and so on. The script might still work fine if the files are using a different name syntax, but most likely something will go wrong if the correct syntax isn't used.
