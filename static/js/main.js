document.addEventListener('DOMContentLoaded', () => {
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const uploadStatus = document.getElementById('uploadStatus');
    const modelSelect = document.getElementById('modelSelect');
    const refreshModelsButton = document.getElementById('refreshModels');
    const analyzeButton = document.getElementById('analyzeButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsDisplay = document.getElementById('resultsDisplay');
    const customItemsInput = document.getElementById('customItems');
    const analysisErrorLog = document.getElementById('analysisErrorLog'); // Get the error log element

    const foundItemsList = document.getElementById('foundItems');
    const maybeFoundItemsList = document.getElementById('maybeFoundItems');
    const notFoundItemsList = document.getElementById('notFoundItems');
    const rawOutputPre = document.getElementById('rawOutput');
    const queriedItemsEchoedList = document.getElementById('queriedItemsEchoed'); // New element

    // Sidebar navigation elements
    const navLinks = document.querySelectorAll('.sidebar ul li a');
    const contentSections = document.querySelectorAll('.content-area section.card');
    const analysisSections = [
        'upload-section', 
        'preview-section', 
        'custom-search-section', 
        'model-selection-section', 
        'analysis-section', 
        'results-section', 
        'threshold-section'
    ];

    const foundThresholdLowInput = document.getElementById('foundThresholdLow');
    const foundThresholdHighInput = document.getElementById('foundThresholdHigh'); // Not directly used in current backend logic but good to have
    const maybeThresholdLowInput = document.getElementById('maybeThresholdLow');
    const maybeThresholdHighInput = document.getElementById('maybeThresholdHigh'); // Not directly used

    let currentUploadedFilePath = null;

    // FR001: Image Upload & FR002: Image Preview
    imageUpload.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadStatus.textContent = 'Uploading...';
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (response.ok) {
                    uploadStatus.textContent = result.message;
                    imagePreview.src = result.filepath; // Display preview
                    imagePreview.style.display = 'block';
                    currentUploadedFilePath = result.filepath;
                    analyzeButton.disabled = false; // Enable analyze button
                } else {
                    uploadStatus.textContent = `Error: ${result.error}`;
                    imagePreview.style.display = 'none';
                    currentUploadedFilePath = null;
                    analyzeButton.disabled = true;
                }
            } catch (error) {
                uploadStatus.textContent = `Upload failed: ${error.message}`;
                imagePreview.style.display = 'none';
                currentUploadedFilePath = null;
                analyzeButton.disabled = true;
            }
        }
    });

    // FR004: Model Selection
    async function fetchAndPopulateModels() {
        try {
            const response = await fetch('/models');
            const result = await response.json();
            if (response.ok) {
                modelSelect.innerHTML = ''; // Clear existing options
                if (result.models && result.models.length > 0) {
                    result.models.forEach(modelName => {
                        const option = document.createElement('option');
                        option.value = modelName;
                        option.textContent = modelName;
                        modelSelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.textContent = 'No models found or Ollama not reachable';
                    option.disabled = true;
                    modelSelect.appendChild(option);
                }
            } else {
                console.error('Failed to fetch models:', result.error);
                const option = document.createElement('option');
                option.textContent = 'Error fetching models';
                option.disabled = true;
                modelSelect.appendChild(option);
            }
        } catch (error) {
            console.error('Error fetching models:', error);
            const option = document.createElement('option');
            option.textContent = 'Error fetching models (network issue)';
            option.disabled = true;
            modelSelect.appendChild(option);
        }
    }
    
    refreshModelsButton.addEventListener('click', fetchAndPopulateModels);
    fetchAndPopulateModels(); // Initial population

    // FR005: Image Analysis & FR003: Local Ollama Integration & FR011: Custom Item Search
    analyzeButton.addEventListener('click', async () => {
        if (!currentUploadedFilePath) {
            alert('Please upload an image first.');
            return;
        }

        loadingIndicator.style.display = 'block';
        resultsDisplay.style.display = 'none'; // Hide previous results
        analysisErrorLog.style.display = 'none'; // Hide previous errors
        analysisErrorLog.textContent = ''; // Clear previous error messages
        foundItemsList.innerHTML = '';
        maybeFoundItemsList.innerHTML = '';
        notFoundItemsList.innerHTML = '';
        rawOutputPre.textContent = '';
        queriedItemsEchoedList.innerHTML = ''; // Clear previous echoed items

        const selectedModel = modelSelect.value;
        const customItems = customItemsInput.value.split(',').map(item => item.trim()).filter(item => item);

        // FR012: Get threshold values from the UI
        const thresholds = {
            found_low: parseFloat(foundThresholdLowInput.value),
            // found_high: parseFloat(foundThresholdHighInput.value), // For future use if needed
            maybe_low: parseFloat(maybeThresholdLowInput.value),
            // maybe_high: parseFloat(maybeThresholdHighInput.value) // For future use if needed
        };

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_path: currentUploadedFilePath,
                    model: selectedModel,
                    custom_items: customItems, // FR011
                    thresholds: thresholds // FR012
                })
            });

            const result = await response.json();
            loadingIndicator.style.display = 'none';

            if (response.ok) {
                resultsDisplay.style.display = 'block';
                rawOutputPre.textContent = result.raw_output || JSON.stringify(result, null, 2);

                // Populate the echoed queried items list
                if (result.queried_items_echoed && result.queried_items_echoed.length > 0) {
                    result.queried_items_echoed.forEach(itemObj => { // Changed from item_name to itemObj
                        const listItem = document.createElement('li');
                        let textContent = itemObj.item;
                        if (itemObj.details) {
                            textContent += ` (${itemObj.details})`;
                        }
                        listItem.textContent = textContent;
                        queriedItemsEchoedList.appendChild(listItem);
                    });
                } else {
                    const listItem = document.createElement('li');
                    listItem.textContent = 'No specific items were listed by the model as being queried.';
                    queriedItemsEchoedList.appendChild(listItem);
                }

                // FR006 & FR007: Populate categorized lists (confidence no longer primary)
                populateResultsList(foundItemsList, result.found, "Found");
                populateResultsList(maybeFoundItemsList, result.maybe_found, "Maybe Found");
                populateResultsList(notFoundItemsList, result.not_found, "Not Found");
                
                // alert("Analysis complete. Parsed results displayed."); // Less intrusive than alert

            } else {
                analysisErrorLog.textContent = `Analysis failed: ${result.error}`;
                analysisErrorLog.style.display = 'block';
            }
        } catch (error) {
            loadingIndicator.style.display = 'none';
            analysisErrorLog.textContent = `Analysis error: ${error.message}`;
            analysisErrorLog.style.display = 'block';
        }
    });

    // Helper function for FR006/FR007
    function populateResultsList(listElement, items, categoryName) {
        listElement.innerHTML = ''; // Clear previous items
        if (items && items.length > 0) {
            items.forEach(itemObj => {
                const listItem = document.createElement('li');
                let textContent = itemObj.item;
                // Confidence is no longer expected from the primary parsing path
                // if (itemObj.confidence !== undefined && itemObj.confidence !== null) { 
                //    textContent += ` (Confidence: ${(itemObj.confidence * 100).toFixed(1)}%)`;
                // }
                if (itemObj.details) { // For unparsed output or extra info
                    textContent += ` - Details: ${itemObj.details}`;
                }
                listItem.textContent = textContent;
                listElement.appendChild(listItem);
            });
        } else {
            const listItem = document.createElement('li');
            listItem.textContent = `No items categorized as '${categoryName}'.`;
            listElement.appendChild(listItem);
        }
    }

    // Sidebar navigation logic
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);

            // Remove active class from all links
            navLinks.forEach(navLink => navLink.classList.remove('active-nav'));
            // Add active class to the clicked link
            link.classList.add('active-nav');

            // Hide all content sections
            contentSections.forEach(section => section.style.display = 'none');

            // Show the target section or all analysis sections if "New Analysis" is clicked
            if (targetId === 'upload-section') {
                analysisSections.forEach(id => {
                    const sectionToShow = document.getElementById(id);
                    if (sectionToShow) sectionToShow.style.display = 'block';
                });
            } else {
                const sectionToShow = document.getElementById(targetId);
                if (sectionToShow) sectionToShow.style.display = 'block';
            }
        });
    });

    // Initially, show the "New Analysis" sections and set the first link as active
    function showInitialView() {
        contentSections.forEach(section => section.style.display = 'none'); // Hide all first
        analysisSections.forEach(id => { // Then show only analysis sections
            const sectionToShow = document.getElementById(id);
            if (sectionToShow) sectionToShow.style.display = 'block';
        });
        const initialActiveLink = document.querySelector('.sidebar ul li a[href="#upload-section"]');
        if (initialActiveLink) initialActiveLink.classList.add('active-nav');
    }

    showInitialView();

});
