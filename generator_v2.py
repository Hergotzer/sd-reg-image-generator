import requests
import base64
import os
import re
import json
import time

def get_user_input(prompt, validation_func=None):
    while True:
        user_input = input(prompt).strip().replace('"', '')  # Remove any quotation marks
        if validation_func is None:
            return user_input
        else:
            try:
                if validation_func(user_input):
                    return user_input
            except Exception as e:
                print(f"Error: {e}")
        print("Invalid input. Please try again.")

def validate_path(path):
    if os.path.exists(path):
        return True
    else:
        raise ValueError(f"Path does not exist: {path}")

def validate_training_set_dir(training_set_dir):
    if os.path.exists(training_set_dir):
        # Check if the directory or its subdirectories contain at least one .txt file
        for root, dirs, files in os.walk(training_set_dir):
            if any(file.endswith('.txt') for file in files):
                return True
        raise ValueError(f"No .txt files found in: {training_set_dir}")
    else:
        raise ValueError(f"Directory does not exist: {training_set_dir}")

def validate_resolution(resolution):
    if resolution.isdigit() and int(resolution) > 0:
        return True
    else:
        raise ValueError("Resolution must be a positive integer.")

def validate_clip_skips(clip_skips):
    try:
        skips = list(map(int, clip_skips.split(',')))
        if all(0 <= skip <= 12 for skip in skips):
            return True
        else:
            raise ValueError("CLIP skips must be integers between 0 and 12.")
    except ValueError:
        raise ValueError("CLIP skips must be a list of integers separated by commas.")

def extract_order(filename):
    # Use regex to find the number after the underscore
    match = re.search(r'_(\d+)', filename)
    return int(match.group(1)) if match else float('inf')  # Return inf if no number is found to push it to the end

def combine_text_files(training_set_dir):
    combined_data = {}

    # Print the main directory path for debugging
    print(f"Training Set Directory: {training_set_dir}")

    if not os.path.exists(training_set_dir):
        print(f"Directory does not exist: {training_set_dir}")
        return combined_data

    # Iterate through each folder in the training_set_dir
    for folder_name in os.listdir(training_set_dir):
        folder_path = os.path.join(training_set_dir, folder_name)

        if os.path.isdir(folder_path):
            print(f"Detected folder: {folder_name}")  # Debugging print

            file_contents = []
            file_names = []
            first_prompt = ""  # To store the content of the first file

            # List all text files and sort them by the number after the underscore
            text_files = sorted((file for file in os.listdir(folder_path) if file.endswith('.txt')), 
                                key=lambda x: int(x.split('-')[-1].split('.')[0]))

            if text_files:
                # Iterate through each sorted file
                for index, file_name in enumerate(text_files):
                    file_path = os.path.join(folder_path, file_name)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()  # Read and strip whitespace
                        file_contents.append(f'"{content}"')  # Wrap content in quotes
                        file_names.append(file_name)

                        # Save the content of the first file separately as the first prompt
                        if index == 0:
                            first_prompt = content  # Save content without quotes for first prompt

                # Combine contents into a single string
                combined_string = ','.join(file_contents)

                # Store the file names, combined string, and first prompt in the dictionary
                combined_data[folder_name] = [file_names, f'{combined_string}', first_prompt]

    return combined_data

def generate_images(url, payload):
    try:
        response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
        print(f"Response Status Code: {response.status_code}")  # Debugging print
        print(f"Response Content: {response.content}")  # Debugging print
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with API request: {e}")
        return {}

def save_images(images, folder_name, file_names, output_dir):
    for i, image_base64 in enumerate(images[1:]):  # Skip the first image
        image_data = base64.b64decode(image_base64)

        # Remove the file extension from the filename if it exists
        file_name_without_extension = os.path.splitext(file_names[i])[0]
        
        filename = f"{file_name_without_extension}.png"
        file_path = os.path.join(output_dir, filename)

        with open(file_path, 'wb') as f:
            f.write(image_data)


def create_output_dir(clip_skip, seed, folder_name):
    output_dir = f"./Results/CLIP-skip_{clip_skip}/seed_{seed}/{folder_name}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def extract_first_prompt(combined_string):
    start_quote = combined_string.find('"') + 1
    end_quote = combined_string.find('"', start_quote)
    first_prompt = combined_string[start_quote:end_quote]
    return first_prompt

# Get user inputs with validation
url = get_user_input("Enter the WEBUI URL: ")

model_path = get_user_input("Enter the location of the model checkpoint: ", validate_path)
model = os.path.basename(model_path)

training_set_dir = get_user_input("Enter the directory containing the training set: ", validate_training_set_dir)

resolution = int(get_user_input("Enter the resolution for the images (one value, in pixels, will be used as both width and height): ", validate_resolution))

seeds = get_user_input("Enter the seed(s) for image generation (separate by commas if multiple): ").split(',')

clip_skips = get_user_input("Enter the CLIP skip(s) (separate by commas if multiple, max value 12): ", validate_clip_skips).split(',')

# Combine text files from the training set directory
combined_data = combine_text_files(training_set_dir)

# Calculate the total number of images to generate
total_images = sum(len(data[0]) for data in combined_data.values()) * len(seeds) * len(clip_skips)  # Total number of images to generate

# Initialize variables for timing and progress tracking
total_start_time = time.time()  # Start timer for the entire process
image_progress = 0
processing_time_accumulated = 0
generation_time_accumulated = 0

# Loop through CLIP skips
for clip_skip in clip_skips:
    # Loop through seeds
    for seed in seeds:
        # Loop through each folder in combined_data
        for folder_name, (file_names, combined_string, first_prompt) in combined_data.items():
            print(f"Starting work on \"{folder_name}\" ({len(file_names)} images to generate), using seed {seed} and CLIP skip of {clip_skip}")

            # Start generation timer
            generation_start_time = time.time()

            # Prepare the payload for the API request
            payload = {
                "prompt": first_prompt,
                "negative_prompt": "",
                "seed": int(seed),
                "sampler_name": "DDIM",
                "steps": 30,
                "width": resolution,
                "height": resolution,
                "cfg_scale": 7,
                "n_iter": 1,
                "batch_size": 1,
                "override_settings": {
                    "sd_model_checkpoint": model,
                    "CLIP_stop_at_last_layers": int(clip_skip),
                },
                "script_name": "x/y/z plot",
                "script_args": [
                    7,
                    combined_string,
                    0,
                    "",
                    0,
                    "",
                    False,
                    False,
                    False,
                    False,
                    True,
                    False,
                    False,
                    False,
                    0
                ]
            }
            
            # Send the payload to the API and receive the response
            payload = json.dumps(payload)
            response = requests.post(url=f'{url}/sdapi/v1/txt2img', data=payload, headers={'Content-Type': 'application/json'})
            response_json = response.json()  # Convert response to JSON
            images = response_json.get('images', [])

            # End generation timer
            generation_end_time = time.time()
            generation_time = generation_end_time - generation_start_time
            generation_time_accumulated += generation_time

            # Save the images
            if images:
                # Start processing timer
                processing_start_time = time.time()

                # Create the output directory
                output_dir = create_output_dir(clip_skip, seed, folder_name)
                save_images(images, folder_name, file_names, output_dir)

                # End processing timer
                processing_end_time = time.time()
                processing_time = processing_end_time - processing_start_time
                processing_time_accumulated += processing_time
                
                # Update progress
                image_progress += len(images)
                
                # Calculate estimated time left
                avg_gen_time_per_image = generation_time_accumulated / image_progress if image_progress > 0 else 0
                avg_proc_time_per_image = processing_time_accumulated / image_progress if image_progress > 0 else 0
                estimated_time_left = (avg_gen_time_per_image + avg_proc_time_per_image) * (total_images - image_progress)

                # Convert estimated time left to hours, minutes, and seconds
                est_hours, est_remainder = divmod(int(estimated_time_left), 3600)
                est_minutes, est_seconds = divmod(est_remainder, 60)

                print(f"{image_progress}/{total_images} images done ({(image_progress / total_images) * 100:.0f}%), estimated time left: {est_hours}:{est_minutes}:{est_seconds}")

# Total time calculation after all images are generated and processed
total_end_time = time.time()
total_time = total_end_time - total_start_time

# Convert total time to hours, minutes, and seconds
total_hours, remainder = divmod(int(total_time), 3600)
total_minutes, total_seconds = divmod(remainder, 60)

# Print the total time taken for the entire process
if total_hours > 0:
    input(f"\nGeneration process completed in {total_hours}:{total_minutes}:{total_seconds}.\nPress any button to exit.")
else:
    input(f"\nGeneration process completed in {total_minutes}:{total_seconds}.\nPress any button to exit.")
