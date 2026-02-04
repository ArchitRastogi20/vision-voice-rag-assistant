/*document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('uploadForm');
    const errorMessage = document.getElementById('errorMessage');
    const cuisineCheckboxes = document.querySelectorAll('input[name="cuisine[]"]');
    let res_feedback;
    let item_feedback;
    let cus_feedback;

    let allSelectedFiles = []; // Initialize the array

    function truncateFilename(filename, maxLength = 15) {
        const [name, ext] = filename.split(/(?=\.[^.]+$)/); // Split at the last dot before the extension
        if (filename.length > maxLength) {
            return name.slice(0, maxLength - ext.length - 3) + '...' + ext;
        }
        return filename;
    }

    // Function to update selected files array
    function updateResultContainer(recipes) {
        const recipeContainer = document.getElementById('resultContainer');

        recipes.recipes.forEach((recipe, index) => {
            const recipeDiv = document.createElement('div');
            recipeDiv.className = 'recipe-card';

            const recipeName = document.createElement('h1');
            recipeName.textContent = recipe.name;
            recipeDiv.appendChild(recipeName);

            const recipeDescription = document.createElement('h2');
            recipeDescription.textContent = recipe.description;
            recipeDiv.appendChild(recipeDescription);

            const ingredientsHeading = document.createElement('h3');
            ingredientsHeading.textContent = 'Ingredients';
            recipeDiv.appendChild(ingredientsHeading);

            const ingredientsList = document.createElement('ul');
            ingredientsList.className = 'ingredients';
            recipe.ingredients.forEach(ingredient => {
                const listItem = document.createElement('li');
                listItem.textContent = ingredient;
                ingredientsList.appendChild(listItem);
            });
            recipeDiv.appendChild(ingredientsList);

            const instructionsDiv = document.createElement('div');
            instructionsDiv.className = 'instructions';
            instructionsDiv.id = `instructions-${index}`;
            instructionsDiv.style.display = 'none';

            const instructionsHeading = document.createElement('h3');
            instructionsHeading.textContent = 'Instructions';
            instructionsDiv.appendChild(instructionsHeading);

            const instructionsList = document.createElement('ul');
            instructionsList.className = 'instructions-list';
            recipe.instructions.forEach(instruction => {
                const listItem = document.createElement('li');
                listItem.textContent = instruction;
                instructionsList.appendChild(listItem);
            });
            instructionsDiv.appendChild(instructionsList);

            recipeDiv.appendChild(instructionsDiv);

            const toggleButton = document.createElement('button');
            toggleButton.className = 'toggle-button';
            toggleButton.textContent = '[See Instructions]';
            toggleButton.onclick = function () {
                const instructions = document.getElementById(`instructions-${index}`);
                if (instructions.style.display === 'none' || instructions.style.display === '') {
                    instructions.style.display = 'block';
                    toggleButton.textContent = '[Hide Instructions]';
                } else {
                    instructions.style.display = 'none';
                    toggleButton.textContent = '[See Instructions]';
                }
            };
            recipeDiv.appendChild(toggleButton);

            // --- NEW: Listen Button with Pause/Play ---
            const listenButton = document.createElement('button');
            listenButton.textContent = '🔊 Listen to Recipe';
            listenButton.className = 'toggle-button';
            listenButton.style.marginLeft = '10px';
            listenButton.style.backgroundColor = '#28a745'; // Green

            // Audio state per recipe card
            let audio = null;
            let isPlaying = false;
            let isPaused = false;

            listenButton.onclick = function () {
                // Case 1: Audio is playing -> Pause it
                if (audio && isPlaying) {
                    audio.pause();
                    isPlaying = false;
                    isPaused = true;
                    listenButton.textContent = '⏸️ Resume'; // Changed icon for clarity
                    listenButton.style.backgroundColor = '#ffc107'; // Yellow/Orange
                    return;
                }

                // Case 2: Audio is paused -> Resume it
                if (audio && isPaused) {
                    audio.play();
                    isPlaying = true;
                    isPaused = false;
                    listenButton.textContent = '🔊 Pause';
                    listenButton.style.backgroundColor = '#17a2b8'; // Blue
                    return;
                }

                // Case 3: Initial Start (audio doesn't exist yet)
                listenButton.disabled = true;
                listenButton.textContent = '⏳ Generating...';

                // Construct text to speak (Name + Ingredients + Instructions)
                const textToSpeak = `${recipe.name}. Ingredients: ${recipe.ingredients.join(', ')}. Instructions: ${recipe.instructions.join('. ')}`;

                fetch('/speak_recipe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: textToSpeak }),
                })
                    .then(response => {
                        if (!response.ok) throw new Error("TTS Failed");
                        return response.blob();
                    })
                    .then(blob => {
                        const audioUrl = URL.createObjectURL(blob);
                        audio = new Audio(audioUrl);

                        audio.play();
                        isPlaying = true;
                        isPaused = false;
                        listenButton.disabled = false;
                        listenButton.textContent = '🔊 Pause';
                        listenButton.style.backgroundColor = '#17a2b8'; // Blue

                        // Handle audio ending
                        audio.onended = () => {
                            isPlaying = false;
                            isPaused = false;
                            listenButton.textContent = '🔊 Listen Again';
                            listenButton.style.backgroundColor = '#28a745'; // Green
                            audio = null; // Reset audio
                        };
                    })
                    .catch(error => {
                        console.error('Error fetching audio:', error);
                        listenButton.textContent = '❌ Error';
                        listenButton.disabled = false;
                        listenButton.style.backgroundColor = '#dc3545'; // Red
                    });
            };
            recipeDiv.appendChild(listenButton);
            // --------------------------

            recipeContainer.appendChild(recipeDiv);
        });

    }
    function updateSelectedFiles(files) {
        allSelectedFiles.push(...files); // Spread operator to push elements of files array individually
    }

    // Add event listener for file input change event
    document.getElementById('imageInput').addEventListener('change', function (event) {
        let selectedFiles = event.target.files;
        const selectedFilesContainer = document.getElementById('selectedFiles');
        const MAX_FILES = 10;
        const MAX_FILE_SIZE_MB = 5;

        // Clear the selected files container
        //selectedFilesContainer.innerHTML = '';

        // Validate the number of selected files
        if (allSelectedFiles.length > MAX_FILES || allSelectedFiles.length + selectedFiles.length > MAX_FILES) {
            alert(`You can select maximum ${MAX_FILES} files.`);
            return;
        }

        // Validate each selected file
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            const fileSizeMB = file.size / (1024 * 1024); // Convert file size to MB

            // Check file size
            if (fileSizeMB > MAX_FILE_SIZE_MB) {
                alert(`File ${file.name} exceeds the maximum file size limit of ${MAX_FILE_SIZE_MB}MB.`);
                return;
            }

            // Create wrapper element for each file name and cross button pair
            const fileWrapper = document.createElement('div');
            fileWrapper.classList.add('file-wrapper');

            // Create elements for file name and cross button
            const fileNameElement = document.createElement('span');
            const closeButton = document.createElement('button');
            closeButton.classList.add('close-button');
            const thumbnailElement = document.createElement('img');

            // Set attributes and text content
            fileNameElement.classList.add('ellipsis');
            const truncatedName = truncateFilename(file.name);
            fileNameElement.textContent = truncatedName;
            closeButton.textContent = '❌';
            closeButton.setAttribute('type', 'button');

            // Read the image file and set it as the source of the thumbnail
            const reader = new FileReader();
            reader.onload = function (event) {
                thumbnailElement.src = event.target.result;
            };
            reader.readAsDataURL(file);
            // Set width and height of the thumbnail
            thumbnailElement.style.width = '100px'; // Set your desired width
            thumbnailElement.style.height = '100px'; // Set your desired height

            closeButton.addEventListener('click', function () {
                // Remove file from selection when cross button is clicked
                fileWrapper.remove();
                // Remove the file from the array of all selected files
                const indexToRemove = allSelectedFiles.indexOf(file);
                if (indexToRemove !== -1) {
                    allSelectedFiles.splice(indexToRemove, 1);
                }
            });

            // Append elements to wrapper container
            fileWrapper.appendChild(thumbnailElement);
            fileWrapper.appendChild(fileNameElement);
            fileWrapper.appendChild(closeButton);

            // Append wrapper container to selectedFilesContainer
            selectedFilesContainer.appendChild(fileWrapper);
        }

        // Call the function to update selected files
        updateSelectedFiles(selectedFiles);
        selectedFiles = '';
        const fileInput = document.getElementById('imageInput');
        fileInput.value = '';
    });

    cuisineCheckboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            // If "Any" checkbox is selected, deselect all other checkboxes
            if (checkbox.value === 'Any' && checkbox.checked) {
                cuisineCheckboxes.forEach(function (cb) {
                    if (cb !== checkbox) {
                        cb.checked = false;
                    }
                });
            } else if (checkbox.value !== 'Any' && checkbox.checked) {
                // If any other checkbox is selected, deselect the "Any" checkbox
                const anyCheckbox = Array.from(cuisineCheckboxes).find(cb => cb.value === 'Any');
                anyCheckbox.checked = false;
            }
        });
    });



    // Add event listener for form submit event
    uploadForm.addEventListener('submit', function (event) {
        // Prevent default form submission behavior
        event.preventDefault();

        // Clear previous error messages
        errorMessage.textContent = '';

        // Check if an image is selected
        if (allSelectedFiles.length === 0) {
            errorMessage.textContent = 'Please select an image.';
            return;
        }

        // Create FormData object
        const formData = new FormData();

        // Append all selected files to FormData object
        allSelectedFiles.forEach(file => {
            formData.append('image', file);
        });

        // Add selected cuisine to FormData object
        const selectedCuisine = [];
        cuisineCheckboxes.forEach(function (checkbox) {
            if (checkbox.checked) {
                selectedCuisine.push(checkbox.value);
            }
        });
        if (selectedCuisine.length === 0) {
            errorMessage.textContent = 'Please select cuisine.';
            return; // Stop further execution
        }
        document.getElementById('submitButton').addEventListener('click', function () {
            // Lock the submit button
            this.disabled = true;
            // Apply shadow effect
            this.classList.add('clicked');
        });

        console.log('cusine', selectedCuisine.join(','))
        formData.append('cuisine', selectedCuisine);
        lockSubmitButton();

        //remove cross buttons
        const closeButtons = document.querySelectorAll('.close-button');
        closeButtons.forEach(button => {
            button.style.display = 'none';
        });

        // Disable all cuisine checkboxes
        //const cuisineCheckboxes = document.querySelectorAll('.cuisine-container input[type="checkbox"]');
        cuisineCheckboxes.forEach(function (checkbox) {
            checkbox.disabled = true;
        });
        // Send form data to predict endpoint
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                document.getElementById('refreshButton').style.display = 'inline-block';
                if ('detected_items' in data && 'recipes' in data) {
                    // Update the content of the resultContainer div with the fetched recipe
                    document.getElementById('resultContainer').style.display = 'block';
                    document.getElementById('itemsContainer').style.display = 'block';
                    // document.getElementById('resultContainer').innerHTML = data.result;
                    res_feedback = data.recipes;
                    item_feedback = data.detected_items;
                    document.getElementById('uploadForm').style.display = 'none';
                    document.getElementById('itemsContainer').innerHTML = data.detected_items.map(item => item.toUpperCase()).join(', ');
                    if (data.empty_img.length > 0) {
                        document.getElementById('undetectedContainer').style.display = 'block';
                        document.getElementById('undetectedContainer').innerText = `Please check these images , I was unable to detect ${data.empty_img}`;
                    }
                    // document.getElementById('feedbackContainer').style.display = 'block';
                    updateResultContainer(data.recipes)
                    var button = document.getElementById("submitButton");
                    button.disabled = true;
                    button.style.backgroundColor = "gray"; // Change the background color to gray
                    button.style.boxShadow = "2px 2px 5px rgba(0, 0, 0, 0.5)"; // Add a shadow
                }
                document.getElementById('uploadForm').style.display = 'none';
                if (data.no_item !== null && typeof data.no_item !== 'undefined') {
                    document.getElementById('itemsContainer').style.display = 'block';
                    console.log(data.no_item)
                    document.getElementById('itemsContainer').innerText = data.no_item;
                    document.getElementById('uploadForm').style.display = 'none';

                }
                if (data.no_img !== null && typeof data.no_img !== 'undefined') {
                    document.getElementById('noimgContainer').style.display = 'block';
                    document.getElementById('noimgContainer').innerText = data.no_img;
                    document.getElementById('uploadForm').style.display = 'none';

                }
                if (data.not_img !== null && typeof data.not_img !== 'undefined') {
                    document.getElementById('notimgContainer').style.display = 'block';
                    document.getElementById('notimgContainer').innerText = data.not_img.not_img;
                    document.getElementById('uploadForm').style.display = 'none';

                }
                if (data.no_ext !== null && typeof data.no_ext !== 'undefined') {
                    document.getElementById('noextContainer').style.display = 'block';
                    document.getElementById('noextContainer').innerText = data.no_ext;
                    document.getElementById('uploadForm').style.display = 'none';

                }
                if (data.invalid_img_ext !== null && typeof data.invalid_img_ext !== 'undefined') {
                    console.log('data.invalid_img_ext:', data.invalid_img_ext);
                    console.log('typeof data.invalid_img_ext:', typeof data.invalid_img_ext);
                    console.log('Condition evaluation:', data.invalid_img_ext !== null && typeof data.invalid_img_ext !== 'undefined');
                    document.getElementById('noimgextContainer').style.display = 'block';
                    document.getElementById('noimgextContainer').innerText = data.invalid_img_ext;
                    document.getElementById('uploadForm').style.display = 'none';

                }
                else {
                    // Unexpected response format
                    console.log(data)
                    console.error('Unexpected response format');
                    document.getElementById('uploadForm').style.display = 'none';
                    document.getElementById('refreshButton').style.display = 'inline-block';
                }
                document.getElementById('submitButton').disabled = true;
            })
            .catch(error => {
                // Display an error message if there was an error fetching the recipe
                document.getElementById('refreshButton').style.display = 'inline-block'; // Move this line here
                console.log(error);
                document.getElementById('errorMessage').innerText = 'Error fetching recipe. Please try again.';
                document.getElementById('uploadForm').style.display = 'none';
                document.getElementById('refreshButton').style.display = 'inline-block'; // Move this line here
            });

        // Submit the form (you can add AJAX code here if needed)
        // uploadForm.submit(); // You can uncomment this line if you want to submit the form
    });

    document.getElementById('submitFeedback').addEventListener('click', function () {
        // Get the feedback from the textarea
        var feedback = document.getElementById('feedback').value;
        // Create a FormData object to send feedback data to the server

        var formData = new FormData();
        formData.append('feedback', feedback);
        formData.append('cus_feedback', cus_feedback);
        formData.append('res_feedback', res_feedback);
        formData.append('item_feedback', item_feedback);
        document.getElementById('feedbackResult').style.display = 'block';
        var button = document.getElementById("submitFeedback");
        button.disabled = true;
        button.style.backgroundColor = "gray"; // Change the background color to gray
        button.style.boxShadow = "2px 2px 5px rgba(0, 0, 0, 0.5)"; // Add a shadow

        // Send feedback data to the server using fetch API
        fetch('/feedback', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text()) // Convert response to text
            .then(data => {
                // Update the feedbackResult container with the response text
                document.getElementById('feedbackResult').innerHTML = data;
            })
            .catch(error => {
                // Display an error message if there was an error fetching the feedback
                console.error('Error fetching feedback:', error);
                document.getElementById('feedbackResult').innerText = 'Error fetching feedback. Please try again later.';
            });
    });

});*/



document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('uploadForm');
    const errorMessage = document.getElementById('errorMessage');
    const cuisineCheckboxes = document.querySelectorAll('input[name="cuisine[]"]');
    let res_feedback;
    let item_feedback;
    let cus_feedback;

    let allSelectedFiles = []; // Initialize the array

    function truncateFilename(filename, maxLength = 15) {
        const [name, ext] = filename.split(/(?=\.[^.]+$)/); // Split at the last dot before the extension
        if (filename.length > maxLength) {
            return name.slice(0, maxLength - ext.length - 3) + '...' + ext;
        }
        return filename;
    }

    // Function to update selected files array
    function updateResultContainer(recipes) {
        const recipeContainer = document.getElementById('resultContainer');

        recipes.recipes.forEach((recipe, index) => {
            const recipeDiv = document.createElement('div');
            recipeDiv.className = 'recipe-card';

            const recipeName = document.createElement('h1');
            recipeName.textContent = recipe.name;
            recipeDiv.appendChild(recipeName);

            const recipeDescription = document.createElement('h2');
            recipeDescription.textContent = recipe.description;
            recipeDiv.appendChild(recipeDescription);

            const ingredientsHeading = document.createElement('h3');
            ingredientsHeading.textContent = 'Ingredients';
            recipeDiv.appendChild(ingredientsHeading);

            const ingredientsList = document.createElement('ul');
            ingredientsList.className = 'ingredients';
            recipe.ingredients.forEach(ingredient => {
                const listItem = document.createElement('li');
                listItem.textContent = ingredient;
                ingredientsList.appendChild(listItem);
            });
            recipeDiv.appendChild(ingredientsList);

            const instructionsDiv = document.createElement('div');
            instructionsDiv.className = 'instructions';
            instructionsDiv.id = `instructions-${index}`;
            instructionsDiv.style.display = 'none';

            const instructionsHeading = document.createElement('h3');
            instructionsHeading.textContent = 'Instructions';
            instructionsDiv.appendChild(instructionsHeading);

            const instructionsList = document.createElement('ul');
            instructionsList.className = 'instructions-list';
            recipe.instructions.forEach(instruction => {
                const listItem = document.createElement('li');
                listItem.textContent = instruction;
                instructionsList.appendChild(listItem);
            });
            instructionsDiv.appendChild(instructionsList);

            recipeDiv.appendChild(instructionsDiv);

            const toggleButton = document.createElement('button');
            toggleButton.className = 'toggle-button';
            toggleButton.textContent = '[See Instructions]';
            toggleButton.onclick = function () {
                const instructions = document.getElementById(`instructions-${index}`);
                if (instructions.style.display === 'none' || instructions.style.display === '') {
                    instructions.style.display = 'block';
                    toggleButton.textContent = '[Hide Instructions]';
                } else {
                    instructions.style.display = 'none';
                    toggleButton.textContent = '[See Instructions]';
                }
            };
            recipeDiv.appendChild(toggleButton);

            // --- NEW: Listen Button with Pause/Play ---
            const listenButton = document.createElement('button');
            listenButton.textContent = '🔊 Listen to Recipe';
            listenButton.className = 'toggle-button';
            listenButton.style.marginLeft = '10px';
            listenButton.style.backgroundColor = '#28a745'; // Green

            // Audio state per recipe card
            let audio = null;
            let isPlaying = false;
            let isPaused = false;

            listenButton.onclick = function () {
                // Case 1: Audio is playing -> Pause it
                if (audio && isPlaying) {
                    audio.pause();
                    isPlaying = false;
                    isPaused = true;
                    listenButton.textContent = '⏸️ Resume'; // Changed icon for clarity
                    listenButton.style.backgroundColor = '#ffc107'; // Yellow/Orange
                    return;
                }

                // Case 2: Audio is paused -> Resume it
                if (audio && isPaused) {
                    audio.play();
                    isPlaying = true;
                    isPaused = false;
                    listenButton.textContent = '🔊 Pause';
                    listenButton.style.backgroundColor = '#17a2b8'; // Blue
                    return;
                }

                // Case 3: Initial Start (audio doesn't exist yet)
                listenButton.disabled = true;
                listenButton.textContent = '⏳ Generating...';

                // Construct text to speak (Name + Ingredients + Instructions)
                const textToSpeak = `${recipe.name}. Ingredients: ${recipe.ingredients.join(', ')}. Instructions: ${recipe.instructions.join('. ')}`;

                fetch('/speak_recipe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: textToSpeak }),
                })
                    .then(response => {
                        if (!response.ok) throw new Error("TTS Failed");
                        return response.blob();
                    })
                    .then(blob => {
                        const audioUrl = URL.createObjectURL(blob);
                        audio = new Audio(audioUrl);

                        audio.play();
                        isPlaying = true;
                        isPaused = false;
                        listenButton.disabled = false;
                        listenButton.textContent = '🔊 Pause';
                        listenButton.style.backgroundColor = '#17a2b8'; // Blue

                        // Handle audio ending
                        audio.onended = () => {
                            isPlaying = false;
                            isPaused = false;
                            listenButton.textContent = '🔊 Listen Again';
                            listenButton.style.backgroundColor = '#28a745'; // Green
                            audio = null; // Reset audio
                        };
                    })
                    .catch(error => {
                        console.error('Error fetching audio:', error);
                        listenButton.textContent = '❌ Error';
                        listenButton.disabled = false;
                        listenButton.style.backgroundColor = '#dc3545'; // Red
                    });
            };
            recipeDiv.appendChild(listenButton);
            // --------------------------

            recipeContainer.appendChild(recipeDiv);
        });

    }
    function updateSelectedFiles(files) {
        allSelectedFiles.push(...files); // Spread operator to push elements of files array individually
    }

    // Add event listener for file input change event
    document.getElementById('imageInput').addEventListener('change', function (event) {
        let selectedFiles = event.target.files;
        const selectedFilesContainer = document.getElementById('selectedFiles');
        const MAX_FILES = 10;
        const MAX_FILE_SIZE_MB = 5;

        // Validate the number of selected files
        if (allSelectedFiles.length > MAX_FILES || allSelectedFiles.length + selectedFiles.length > MAX_FILES) {
            alert(`You can select maximum ${MAX_FILES} files.`);
            return;
        }

        // Validate each selected file
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            const fileSizeMB = file.size / (1024 * 1024); // Convert file size to MB

            // Check file size
            if (fileSizeMB > MAX_FILE_SIZE_MB) {
                alert(`File ${file.name} exceeds the maximum file size limit of ${MAX_FILE_SIZE_MB}MB.`);
                return;
            }

            // Create wrapper element for each file name and cross button pair
            const fileWrapper = document.createElement('div');
            fileWrapper.classList.add('file-wrapper');

            // Create elements for file name and cross button
            const fileNameElement = document.createElement('span');
            const closeButton = document.createElement('button');
            closeButton.classList.add('close-button');
            const thumbnailElement = document.createElement('img');

            // Set attributes and text content
            fileNameElement.classList.add('ellipsis');
            const truncatedName = truncateFilename(file.name);
            fileNameElement.textContent = truncatedName;
            closeButton.textContent = '❌';
            closeButton.setAttribute('type', 'button');

            // Read the image file and set it as the source of the thumbnail
            const reader = new FileReader();
            reader.onload = function (event) {
                thumbnailElement.src = event.target.result;
            };
            reader.readAsDataURL(file);
            // Set width and height of the thumbnail
            thumbnailElement.style.width = '100px';
            thumbnailElement.style.height = '100px';

            closeButton.addEventListener('click', function () {
                // Remove file from selection when cross button is clicked
                fileWrapper.remove();
                // Remove the file from the array of all selected files
                const indexToRemove = allSelectedFiles.indexOf(file);
                if (indexToRemove !== -1) {
                    allSelectedFiles.splice(indexToRemove, 1);
                }
            });

            // Append elements to wrapper container
            fileWrapper.appendChild(thumbnailElement);
            fileWrapper.appendChild(fileNameElement);
            fileWrapper.appendChild(closeButton);

            // Append wrapper container to selectedFilesContainer
            selectedFilesContainer.appendChild(fileWrapper);
        }

        // Call the function to update selected files
        updateSelectedFiles(selectedFiles);
        selectedFiles = '';
        const fileInput = document.getElementById('imageInput');
        fileInput.value = '';
    });

    cuisineCheckboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            // If "Any" checkbox is selected, deselect all other checkboxes
            if (checkbox.value === 'Any' && checkbox.checked) {
                cuisineCheckboxes.forEach(function (cb) {
                    if (cb !== checkbox) {
                        cb.checked = false;
                    }
                });
            } else if (checkbox.value !== 'Any' && checkbox.checked) {
                // If any other checkbox is selected, deselect the "Any" checkbox
                const anyCheckbox = Array.from(cuisineCheckboxes).find(cb => cb.value === 'Any');
                anyCheckbox.checked = false;
            }
        });
    });

    // Add event listener for form submit event
    uploadForm.addEventListener('submit', function (event) {
        // Prevent default form submission behavior
        event.preventDefault();

        // Clear previous error messages
        errorMessage.textContent = '';

        // Check if an image is selected
        if (allSelectedFiles.length === 0) {
            errorMessage.textContent = 'Please select an image.';
            return;
        }

        // Create FormData object
        const formData = new FormData();

        // Append all selected files to FormData object
        allSelectedFiles.forEach(file => {
            formData.append('image', file);
        });

        // Add selected cuisine to FormData object
        const selectedCuisine = [];
        cuisineCheckboxes.forEach(function (checkbox) {
            if (checkbox.checked) {
                selectedCuisine.push(checkbox.value);
            }
        });
        if (selectedCuisine.length === 0) {
            errorMessage.textContent = 'Please select cuisine.';
            return; // Stop further execution
        }
        document.getElementById('submitButton').addEventListener('click', function () {
            // Lock the submit button
            this.disabled = true;
            // Apply shadow effect
            this.classList.add('clicked');
        });

        console.log('cusine', selectedCuisine.join(','))
        formData.append('cuisine', selectedCuisine);
        lockSubmitButton();

        //remove cross buttons
        const closeButtons = document.querySelectorAll('.close-button');
        closeButtons.forEach(button => {
            button.style.display = 'none';
        });

        // Disable all cuisine checkboxes
        cuisineCheckboxes.forEach(function (checkbox) {
            checkbox.disabled = true;
        });

        // Send form data to predict endpoint
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                document.getElementById('refreshButton').style.display = 'inline-block';
                if ('detected_items' in data && 'recipes' in data) {
                    document.getElementById('resultContainer').style.display = 'block';
                    document.getElementById('itemsContainer').style.display = 'block';
                    res_feedback = data.recipes;
                    item_feedback = data.detected_items;
                    document.getElementById('uploadForm').style.display = 'none';
                    document.getElementById('itemsContainer').innerHTML = data.detected_items.map(item => item.toUpperCase()).join(', ');
                    if (data.empty_img.length > 0) {
                        document.getElementById('undetectedContainer').style.display = 'block';
                        document.getElementById('undetectedContainer').innerText = `Please check these images , I was unable to detect ${data.empty_img}`;
                    }
                    updateResultContainer(data.recipes)
                    var button = document.getElementById("submitButton");
                    button.disabled = true;
                    button.style.backgroundColor = "gray";
                    button.style.boxShadow = "2px 2px 5px rgba(0, 0, 0, 0.5)";
                }
                document.getElementById('uploadForm').style.display = 'none';
                if (data.no_item !== null && typeof data.no_item !== 'undefined') {
                    document.getElementById('itemsContainer').style.display = 'block';
                    document.getElementById('itemsContainer').innerText = data.no_item;
                    document.getElementById('uploadForm').style.display = 'none';
                }
                if (data.no_img !== null && typeof data.no_img !== 'undefined') {
                    document.getElementById('noimgContainer').style.display = 'block';
                    document.getElementById('noimgContainer').innerText = data.no_img;
                    document.getElementById('uploadForm').style.display = 'none';
                }
                if (data.not_img !== null && typeof data.not_img !== 'undefined') {
                    document.getElementById('notimgContainer').style.display = 'block';
                    document.getElementById('notimgContainer').innerText = data.not_img.not_img;
                    document.getElementById('uploadForm').style.display = 'none';
                }
                if (data.no_ext !== null && typeof data.no_ext !== 'undefined') {
                    document.getElementById('noextContainer').style.display = 'block';
                    document.getElementById('noextContainer').innerText = data.no_ext;
                    document.getElementById('uploadForm').style.display = 'none';
                }
                if (data.invalid_img_ext !== null && typeof data.invalid_img_ext !== 'undefined') {
                    document.getElementById('noimgextContainer').style.display = 'block';
                    document.getElementById('noimgextContainer').innerText = data.invalid_img_ext;
                    document.getElementById('uploadForm').style.display = 'none';
                }
                else {
                    console.log(data)
                    console.error('Unexpected response format');
                    document.getElementById('uploadForm').style.display = 'none';
                    document.getElementById('refreshButton').style.display = 'inline-block';
                }
                document.getElementById('submitButton').disabled = true;
            })
            .catch(error => {
                document.getElementById('refreshButton').style.display = 'inline-block';
                console.log(error);
                document.getElementById('errorMessage').innerText = 'Error fetching recipe. Please try again.';
                document.getElementById('uploadForm').style.display = 'none';
                document.getElementById('refreshButton').style.display = 'inline-block';
            });
    });

    document.getElementById('submitFeedback').addEventListener('click', function () {
        var feedback = document.getElementById('feedback').value;

        var formData = new FormData();
        formData.append('feedback', feedback);
        formData.append('cus_feedback', cus_feedback);
        formData.append('res_feedback', res_feedback);
        formData.append('item_feedback', item_feedback);
        document.getElementById('feedbackResult').style.display = 'block';
        var button = document.getElementById("submitFeedback");
        button.disabled = true;
        button.style.backgroundColor = "gray";
        button.style.boxShadow = "2px 2px 5px rgba(0, 0, 0, 0.5)";

        fetch('/feedback', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text())
            .then(data => {
                document.getElementById('feedbackResult').innerHTML = data;
            })
            .catch(error => {
                console.error('Error fetching feedback:', error);
                document.getElementById('feedbackResult').innerText = 'Error fetching feedback. Please try again later.';
            });
    });

});

