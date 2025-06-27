document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chatWindow');
    const userMessageInput = document.getElementById('userMessageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const systemPromptSelect = document.getElementById('systemPromptSelect');
    const newConversationBtn = document.getElementById('newConversationBtn');
    const geminiApiKeyInput = document.getElementById('geminiApiKey');
    const conversationsList = document.getElementById('conversationsList');
    const newPromptNameInput = document.getElementById('newPromptName');
    const newPromptContentTextarea = document.getElementById('newPromptContent');
    const savePromptBtn = document.getElementById('savePromptBtn');
    const savedPromptsList = document.getElementById('savedPromptsList');
    const darkModeToggle = document.getElementById('darkModeToggle');

    let currentConversationId = null;

    // Default prompts (will be added to the select always)
    const defaultPrompts = [
        { name: 'Helpful AI Assistant', content: 'You are a helpful AI assistant. Please format your responses using Markdown.' },
        { name: 'Creative Writing Assistant', content: 'You are a creative writing assistant. Please format your responses using Markdown.' },
        { name: 'Coding Expert', content: 'You are a coding expert. Please format your responses using Markdown, especially for code blocks.' },
        { name: 'Concise Chatbot', content: 'You are a friendly chatbot that provides concise answers. Please format your responses using Markdown.' }
    ];

    // Function to format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString(); // Adjust as needed for desired format
    }

    // Function to display a message in the chat window
    function displayMessage(message) {
        const { sender, content, timestamp, id, liked, disliked } = message;

        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        if (id) {
            messageElement.dataset.messageId = id;
        }

        // Apply markdown formatting for AI messages
        const contentContainer = document.createElement('div');
        if (sender === 'ai') {
            // Ensure marked.js is loaded before attempting to parse
            if (typeof marked !== 'undefined') {
                contentContainer.innerHTML = marked.parse(content);
            } else {
                console.warn('marked.js not loaded. AI message displayed as plain text.');
                contentContainer.textContent = content;
            }
        } else {
            contentContainer.textContent = content;
        }
        messageElement.appendChild(contentContainer);

        if (timestamp) {
            const timestampElement = document.createElement('span');
            timestampElement.classList.add('timestamp');
            timestampElement.textContent = formatTimestamp(timestamp);
            messageElement.appendChild(timestampElement);
        }

        // Add feedback buttons for AI messages that have an ID
        if (sender === 'ai' && id) {
            const feedbackContainer = document.createElement('div');
            feedbackContainer.classList.add('feedback-container');

            const likeBtn = document.createElement('button');
            likeBtn.classList.add('feedback-btn', 'like-btn');
            if (liked) likeBtn.classList.add('active');
            likeBtn.innerHTML = '👍';
            likeBtn.addEventListener('click', () => handleFeedback(id, 'like'));

            const dislikeBtn = document.createElement('button');
            dislikeBtn.classList.add('feedback-btn', 'dislike-btn');
            if (disliked) dislikeBtn.classList.add('active');
            dislikeBtn.innerHTML = '👎';
            dislikeBtn.addEventListener('click', () => handleFeedback(id, 'dislike'));

            feedbackContainer.appendChild(likeBtn);
            feedbackContainer.appendChild(dislikeBtn);
            messageElement.appendChild(feedbackContainer);
        }

        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Scroll to bottom
    }

    // Function to handle message feedback (like/dislike)
    async function handleFeedback(messageId, feedbackType) {
        const messageElement = document.querySelector(`.message[data-message-id='${messageId}']`);
        if (!messageElement) return;

        const likeBtn = messageElement.querySelector('.like-btn');
        const dislikeBtn = messageElement.querySelector('.dislike-btn');

        let newLikedState = false;
        let newDislikedState = false;

        // Determine the new state based on which button was clicked
        if (feedbackType === 'like') {
            // Toggle like: if it's already active, we're un-liking it. Otherwise, we're liking it.
            newLikedState = !likeBtn.classList.contains('active');
        } else if (feedbackType === 'dislike') {
            // Toggle dislike
            newDislikedState = !dislikeBtn.classList.contains('active');
        }

        try {
            const response = await fetch(`/api/message/${messageId}/feedback`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ liked: newLikedState, disliked: newDislikedState }),
            });

            if (!response.ok) {
                throw new Error('Failed to submit feedback.');
            }

            const updatedMessage = await response.json();

            // Update UI based on the authoritative response from the server
            likeBtn.classList.toggle('active', updatedMessage.liked);
            dislikeBtn.classList.toggle('active', updatedMessage.disliked);

        } catch (error) {
            console.error('Error submitting feedback:', error);
            displayMessage({ sender: 'ai', content: 'Could not save feedback. Please try again.' });
        }
    }

    // Function to fetch and display messages for a conversation
    async function fetchMessages(conversationId) {
        try {
            const response = await fetch(`/api/conversation/${conversationId}/messages`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();
            chatWindow.innerHTML = ''; // Clear existing messages
            messages.forEach(msg => {
                displayMessage(msg);
            });
            currentConversationId = conversationId; // Set current conversation
            // Highlight the active conversation in the sidebar
            document.querySelectorAll('#conversationsList li').forEach(item => {
                item.classList.remove('active');
                if (parseInt(item.dataset.conversationId) === conversationId) {
                    item.classList.add('active');
                }
            });
            displayMessage({ sender: 'ai', content: `Loaded conversation.`});
        } catch (error) {
            console.error('Error fetching messages:', error);
            displayMessage({ sender: 'ai', content: 'Error loading messages. Please try starting a new conversation.'});
        }
    }

    // Function to load and display conversation history in the sidebar
    async function loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const conversations = await response.json();
            conversationsList.innerHTML = ''; // Clear existing list
            if (conversations.length === 0) {
                const noConvoItem = document.createElement('li');
                noConvoItem.textContent = 'No past conversations.';
                conversationsList.appendChild(noConvoItem);
                return;
            }

            conversations.forEach(convo => {
                const listItem = document.createElement('li');
                listItem.dataset.conversationId = convo.id; // Store ID for easy access
                const promptSnippet = convo.system_prompt_used.substring(0, 30) + '...';
                const date = new Date(convo.created_at).toLocaleDateString();
                // Add delete button
                listItem.innerHTML = `<span>${promptSnippet}</span><span class="date-span">${date}</span><button class="delete-btn" data-id="${convo.id}">🗑️</button>`;

                listItem.addEventListener('click', (event) => {
                    // Only fetch messages if the click wasn't on the delete button
                    if (event.target.closest('.delete-btn')) return;
                    fetchMessages(convo.id);
                });

                // Add event listener for the delete button
                const deleteBtn = listItem.querySelector('.delete-btn');
                deleteBtn.addEventListener('click', (event) => {
                    event.stopPropagation(); // Prevent the parent <li>'s click event
                    deleteConversation(convo.id);
                });

                conversationsList.appendChild(listItem);
            });

            // If there's an active conversation, highlight it
            if (currentConversationId) {
                document.querySelectorAll('#conversationsList li').forEach(item => {
                    item.classList.remove('active');
                    if (parseInt(item.dataset.conversationId) === currentConversationId) {
                        item.classList.add('active');
                    }
                });
            }

        } catch (error) {
            console.error('Error loading conversations:', error);
            const errorItem = document.createElement('li');
            errorItem.textContent = 'Error loading conversations.';
            conversationsList.appendChild(errorItem);
        }
    }

    // Function to load and display system prompts
    async function loadPrompts() {
        try {
            const response = await fetch('/api/prompts');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const savedPrompts = await response.json();

            // Clear existing options and list items
            systemPromptSelect.innerHTML = '';
            savedPromptsList.innerHTML = '';

            // Add default prompts to the select dropdown
            defaultPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.content;
                option.textContent = `Default: ${prompt.name}`;
                systemPromptSelect.appendChild(option);
            });

            // Add saved prompts to the select dropdown and the management list
            if (savedPrompts.length > 0) {
                const savedPromptsOptGroup = document.createElement('optgroup');
                savedPromptsOptGroup.label = 'Your Saved Prompts';
                systemPromptSelect.appendChild(savedPromptsOptGroup);

                savedPrompts.forEach(prompt => {
                    // Add to select dropdown
                    const option = document.createElement('option');
                    option.value = prompt.content;
                    option.textContent = `${prompt.name}`;
                    option.dataset.promptId = prompt.id; // Store ID for potential future use (e.g., editing)
                    savedPromptsOptGroup.appendChild(option);

                    // Add to saved prompts list for management
                    const listItem = document.createElement('li');
                    listItem.dataset.promptId = prompt.id;
                    listItem.innerHTML = `<span>${prompt.name}</span><button class="delete-btn" data-id="${prompt.id}">🗑️</button>`;
                    
                    // Add event listener for delete button
                    const deleteBtn = listItem.querySelector('.delete-btn');
                    deleteBtn.addEventListener('click', (event) => {
                        event.stopPropagation();
                        deletePrompt(prompt.id);
                    });
                    savedPromptsList.appendChild(listItem);
                });
            } else {
                const noPromptItem = document.createElement('li');
                noPromptItem.textContent = 'No custom prompts saved.';
                savedPromptsList.appendChild(noPromptItem);
            }

        } catch (error) {
            console.error('Error loading prompts:', error);
            const errorItem = document.createElement('li');
            errorItem.textContent = 'Error loading custom prompts.';
            savedPromptsList.appendChild(errorItem);
            systemPromptSelect.innerHTML = '<option>Error loading prompts</option>';
        }
    }

    // Function to save a new prompt
    async function saveNewPrompt() {
        const name = newPromptNameInput.value.trim();
        const content = newPromptContentTextarea.value.trim();

        if (!name || !content) {
            displayMessage({ sender: 'ai', content: 'Please provide both a name and content for the new prompt.' });
            return;
        }

        try {
            const response = await fetch('/api/prompts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, content }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}. Detail: ${errorData.detail || 'Unknown error'}`);
            }

            const newPrompt = await response.json();
            displayMessage({ sender: 'ai', content: `Prompt "${newPrompt.name}" saved successfully.` });
            newPromptNameInput.value = '';
            newPromptContentTextarea.value = '';
            await loadPrompts(); // Reload prompts to show the new one
        } catch (error) {
            console.error('Error saving new prompt:', error);
            displayMessage({ sender: 'ai', content: `Error saving prompt: ${error.message}.` });
        }
    }

    // Function to delete a prompt
    async function deletePrompt(promptId) {
        if (!confirm('Are you sure you want to delete this prompt?')) {
            return;
        }
        try {
            const response = await fetch(`/api/prompts/${promptId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            displayMessage({ sender: 'ai', content: `Prompt deleted.` });
            await loadPrompts(); // Reload prompts list
        } catch (error) {
            console.error('Error deleting prompt:', error);
            displayMessage({ sender: 'ai', content: 'Error deleting prompt. Please try again.' });
        }
    }

    // Function to start a new conversation
    async function startNewConversation() {
        const selectedPromptContent = systemPromptSelect.value;
        const apiKey = geminiApiKeyInput.value.trim();

        if (!apiKey) {
            displayMessage({ sender: 'ai', content: 'Please enter your Gemini API Key before starting a new conversation.' });
            return;
        }

        try {
            const response = await fetch('/api/conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ system_prompt_used: selectedPromptContent }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const conversation = await response.json();
            currentConversationId = conversation.id;
            chatWindow.innerHTML = ''; // Clear chat window for new conversation
            displayMessage({ sender: 'ai', content: `New conversation started with prompt: "${systemPromptSelect.options[systemPromptSelect.selectedIndex].text}"` });
            console.log('New conversation started:', conversation);
            await loadConversations(); // Reload conversations to show the new one

        } catch (error) {
            console.error('Error starting new conversation:', error);
            displayMessage({ sender: 'ai', content: 'Error starting new conversation. Please try again.' });
        }
    }

    // Function to send a user message and get AI response
    async function sendMessage() {
        const messageContent = userMessageInput.value.trim();
        const apiKey = geminiApiKeyInput.value.trim();

        if (!messageContent) return;
        if (currentConversationId === null) {
            displayMessage({ sender: 'ai', content: 'Please start a new conversation first.' });
            return;
        }
        if (!apiKey) {
            displayMessage({ sender: 'ai', content: 'Please enter your Gemini API Key before sending a message.' });
            return;
        }

        displayMessage({ sender: 'user', content: messageContent, timestamp: new Date().toISOString() }); // Display user message immediately
        userMessageInput.value = ''; // Clear input field

        try {
            const response = await fetch(`/api/conversation/${currentConversationId}/send_message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message_content: messageContent, api_key: apiKey }),
            });

            if (!response.ok) {
                 const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}. Detail: ${errorData.detail || 'Failed to get AI response.'}`);
            }

            const aiMessage = await response.json();
            displayMessage(aiMessage);
        } catch (error) {
            console.error('Error sending message or getting AI response:', error);
            displayMessage({ sender: 'ai', content: `Error: ${error.message}` });
        }
    }

    // New function to delete a conversation
    async function deleteConversation(conversationId) {
        if (!confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
            return;
        }
        try {
            const response = await fetch(`/api/conversation/${conversationId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            displayMessage({ sender: 'ai', content: `Conversation deleted.` });
            if (currentConversationId === conversationId) {
                currentConversationId = null;
                chatWindow.innerHTML = ''; // Clear chat window
                displayMessage({ sender: 'ai', content: 'Conversation deleted. Please start a new conversation.' });
            }
            await loadConversations(); // Reload conversations list
        } catch (error) {
            console.error('Error deleting conversation:', error);
            displayMessage({ sender: 'ai', content: 'Error deleting conversation. Please try again.' });
        }
    }

    // Dark Mode Toggle Logic
    function applyDarkMode(isDark) {
        if (isDark) {
            document.body.classList.add('dark-mode');
            darkModeToggle.textContent = 'Toggle Light Mode';
        } else {
            document.body.classList.remove('dark-mode');
            darkModeToggle.textContent = 'Toggle Dark Mode';
        }
    }

    // Check for saved dark mode preference on load
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'enabled') {
        applyDarkMode(true);
    } else {
        applyDarkMode(false);
    }

    darkModeToggle.addEventListener('click', () => {
        const isCurrentlyDark = document.body.classList.contains('dark-mode');
        if (isCurrentlyDark) {
            applyDarkMode(false);
            localStorage.setItem('darkMode', 'disabled');
        } else {
            applyDarkMode(true);
            localStorage.setItem('darkMode', 'enabled');
        }
    });

    // Event Listeners
    newConversationBtn.addEventListener('click', startNewConversation);
    sendMessageBtn.addEventListener('click', sendMessage);
    userMessageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    savePromptBtn.addEventListener('click', saveNewPrompt);

    // Initial setup: Load past conversations and prompt the user
    loadConversations();
    loadPrompts(); // Load prompts on startup
    displayMessage({ sender: 'ai', content: 'Welcome to PromptCraft AI Chat! Please enter your Gemini API Key, then choose a system prompt and click "Start New Conversation" to begin.' });
});