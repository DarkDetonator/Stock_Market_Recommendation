document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Functionality
    function toggleTheme() {
        const body = document.body;
        const isDark = body.classList.contains('dark');
        const themeToggleButton = document.querySelector('.theme-toggle i');
        if (isDark) {
            body.classList.remove('dark');
            body.classList.add('light');
            themeToggleButton.classList.remove('fa-sun');
            themeToggleButton.classList.add('fa-moon');
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.remove('light');
            body.classList.add('dark');
            themeToggleButton.classList.remove('fa-moon');
            themeToggleButton.classList.add('fa-sun');
            localStorage.setItem('theme', 'dark');
        }
        // Refresh the recommendations graph with the new theme
        if (hasPredictionRun) {
            loadRecommendations();
        }
    }

    // Load the saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const body = document.body;
    const themeToggleButton = document.querySelector('.theme-toggle i');
    body.classList.add(savedTheme);
    if (savedTheme === 'dark') {
        themeToggleButton.classList.add('fa-sun');
    } else {
        themeToggleButton.classList.add('fa-moon');
    }

    // Add event listener for theme toggle button
    document.querySelector('.theme-toggle').addEventListener('click', toggleTheme);

    // Navigation
    const navLinks = document.querySelectorAll('nav ul li a');
    const sections = document.querySelectorAll('main section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').slice(1);
            
            navLinks.forEach(item => {
                item.parentElement.classList.remove('active');
            });
            link.parentElement.classList.add('active');
            
            sections.forEach(section => {
                section.classList.remove('active-section');
                if (section.id === targetId) {
                    section.classList.add('active-section');
                }
            });
        });
    });
    
    // Chat functionality
    const chatMessages = document.getElementById('chatMessages');
    const userMessageInput = document.getElementById('userMessage');
    const sendButton = document.getElementById('sendButton');
    const clearChatButton = document.createElement('button');
    
    clearChatButton.id = 'clearChatButton';
    clearChatButton.className = 'btn';
    clearChatButton.innerHTML = '<i class="fas fa-trash-alt"></i> Clear Chat';
    document.querySelector('.chat-card .card-header').appendChild(clearChatButton);
    
    let isChatCleared = false;
    let hasPredictionRun = false; // Track if prediction has been run
    
    // Check if marked and DOMPurify are available
    const isMarkdownSupported = typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined';
    if (!isMarkdownSupported) {
        showNotification('Warning', 'Markdown rendering is unavailable. Messages will be displayed as plain text.', 'warning');
    }
    
    // Function to add a message to the chat
    function addMessage(message, isUser = false, retryCallback = null) {
        if (isChatCleared) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'} fade-in`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isUser) {
            messageContent.textContent = message;
        } else {
            if (isMarkdownSupported) {
                const htmlContent = marked.parse(message);
                const sanitizedHtml = DOMPurify.sanitize(htmlContent);
                messageContent.innerHTML = sanitizedHtml;
                
                const links = messageContent.querySelectorAll('a');
                links.forEach(link => {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                    link.addEventListener('click', () => {
                        console.log(`User clicked news link: ${link.href}`);
                    });
                });
                
                const financialSection = messageContent.querySelector('h1:first-of-type');
                if (financialSection && financialSection.textContent.includes('Financial Overview')) {
                    const financialContent = financialSection.nextElementSibling.nextElementSibling;
                    if (financialContent) {
                        const copyButton = document.createElement('button');
                        copyButton.className = 'copy-button';
                        copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
                        copyButton.addEventListener('click', () => {
                            const textToCopy = Array.from(financialContent.childNodes)
                                .filter(node => node.nodeType === Node.TEXT_NODE || (node.nodeName === 'P' && node.textContent.trim()))
                                .map(node => node.textContent.trim())
                                .join('\n');
                            navigator.clipboard.writeText(textToCopy).then(() => {
                                showNotification('Success', 'Financial data copied to clipboard!', 'success');
                            }).catch(() => {
                                showNotification('Error', 'Failed to copy financial data.', 'error');
                            });
                        });
                        financialSection.appendChild(copyButton);
                    }
                }
                
                const newsSection = messageContent.querySelector('h1:last-of-type');
                if (newsSection && newsSection.textContent.includes('Recent News')) {
                    const newsContent = newsSection.nextElementSibling.nextElementSibling;
                    if (newsContent && newsContent.textContent.includes('No recent news found') && retryCallback) {
                        const retryButton = document.createElement('button');
                        retryButton.className = 'retry-button';
                        retryButton.innerHTML = '<i class="fas fa-redo"></i> Retry';
                        retryButton.addEventListener('click', retryCallback);
                        newsContent.appendChild(retryButton);
                    }
                }
            } else {
                // Fallback to plain text if Markdown is not supported
                messageContent.textContent = message;
            }
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    function fetchNewsForCompany(company) {
        return fetch('/api/scrape_news', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ company })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // After scraping, fetch the updated news
                return fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: company })
                })
                .then(response => response.json())
                .then(chatData => {
                    if (chatData.success) {
                        return chatData.response;
                    } else {
                        throw new Error(chatData.error || 'Failed to fetch updated news');
                    }
                });
            } else {
                throw new Error(data.error || 'Failed to scrape news');
            }
        });
    }
    
    function sendMessage() {
        const message = userMessageInput.value.trim();
        if (!message) return;
        
        addMessage(message, true);
        userMessageInput.value = '';
        
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'message bot';
        loadingMessage.innerHTML = '<div class="message-content">Typing...</div>';
        chatMessages.appendChild(loadingMessage);
        
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            if (chatMessages.contains(loadingMessage)) {
                chatMessages.removeChild(loadingMessage);
            }
            
            const retryCallback = data.company ? () => {
                if (isChatCleared) return;
                addMessage('Retrying to fetch news...', false);
                fetchNewsForCompany(data.company)
                    .then(newsResponse => {
                        if (isChatCleared) return;
                        const lastBotMessage = chatMessages.querySelector('.message.bot:last-of-type');
                        if (lastBotMessage) {
                            chatMessages.removeChild(lastBotMessage);
                        }
                        addMessage(newsResponse, false, retryCallback);
                    })
                    .catch(error => {
                        if (isChatCleared) return;
                        addMessage(`Error: Failed to fetch news. ${error.message}`, false, retryCallback);
                    });
            } : null;
            
            addMessage(data.response, false, retryCallback);
            if (data.company) {
                companySelect.value = data.company;
                const companySector = companiesData.find(c => c.ticker === data.company)?.sector || '';
                predictionSectorSelect.value = companySector;
                stockSectorSelect.value = companySector;
                updateCompanySelect(companySector);
                companySelect.dispatchEvent(new Event('change'));
                const predictionLink = document.querySelector('nav ul li a[href="#predictions"]');
                if (predictionLink) predictionLink.click();
                showNotification(`Info`, `Showing predictions for ${data.company}`, 'info');
            }
        })
        .catch(error => {
            if (chatMessages.contains(loadingMessage)) {
                chatMessages.removeChild(loadingMessage);
            }
            addMessage('Sorry, there was an error processing your request. Please try again.', false);
            showNotification('Error', 'Failed to get a response from the server.', 'error');
            console.error('Error:', error);
        });
    }
    
    sendButton.addEventListener('click', sendMessage);
    
    userMessageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    clearChatButton.addEventListener('click', () => {
        chatMessages.innerHTML = '';
        isChatCleared = true;
        showNotification('Success', 'Chat cleared successfully.', 'success');
        setTimeout(() => {
            isChatCleared = false;
        }, 1000);
    });
    
    const companySelect = document.getElementById('companySelect');
    const predictionDetails = document.getElementById('predictionDetails');
    const stockSectorSelect = document.getElementById('stockSectorSelect');
    const predictionSectorSelect = document.getElementById('predictionSectorSelect');
    let companiesData = [];

    // Fetch Sectors
    function loadSectors() {
        console.log('Fetching sectors from /api/sectors');
        fetch('/api/sectors')
            .then(response => response.json())
            .then(data => {
                console.log('Sectors received:', data);
                const sectors = data.sectors || [];
                [stockSectorSelect, predictionSectorSelect].forEach(select => {
                    select.innerHTML = '<option value="">All Sectors</option>';
                    sectors.forEach(sector => {
                        const option = document.createElement('option');
                        option.value = sector;
                        option.textContent = sector;
                        select.appendChild(option);
                    });
                });
            })
            .catch(error => {
                console.error('Error fetching sectors:', error);
                showNotification('Error', 'Failed to load sectors. Please try again.', 'error');
            });
    }

    // Load Companies with Sector Data
    function loadCompanies() {
        console.log('Fetching companies from /api/companies');
        fetch('/api/companies')
            .then(response => response.json())
            .then(data => {
                console.log('Companies received:', data);
                companiesData = data.companies || [];
                updateCompanySelect('');
            })
            .catch(error => {
                console.error('Error loading companies:', error);
                showNotification('Error', 'Failed to load companies list. Please try again.', 'error');
            });
    }

    // Update Company Selector Based on Sector
    function updateCompanySelect(selectedSector) {
        console.log('Updating company select for sector:', selectedSector);
        companySelect.innerHTML = '<option value="">-- Select a company --</option>';
        const filteredCompanies = selectedSector
            ? companiesData.filter(company => company.sector === selectedSector)
            : companiesData;
        console.log('Filtered companies:', filteredCompanies);
        filteredCompanies.forEach(company => {
            const option = document.createElement('option');
            option.value = company.ticker;
            option.textContent = company.name;
            companySelect.appendChild(option);
        });
    }
    
    function fetchCompanyPrediction(company) {
        console.log('Fetching prediction for company:', company);
        predictionDetails.classList.remove('hidden');
        document.getElementById('growthComparisonChart').innerHTML = '<div class="loading">Loading prediction data...</div>';
        document.getElementById('recommendationGaugeChart').innerHTML = '<div class="loading">Loading recommendation data...</div>';
        
        fetch(`/api/prediction/${company}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification('No Data', `No prediction data available for ${company}.`, 'info');
                    predictionDetails.classList.add('hidden');
                    return;
                }
                
                predictionDetails.classList.remove('hidden');
                
                const predictionData = Array.isArray(data.prediction) ? data.prediction[0] : data.prediction;
                
                document.getElementById('predictedGrowthValue').textContent = formatScore(predictionData.predicted_growth_score);
                document.getElementById('previousGrowthValue').textContent = formatScore(predictionData.previous_predicted_growth_score || 0);
                
                const change = predictionData.prediction_change || (predictionData.predicted_growth_score - (predictionData.previous_predicted_growth_score || 0));
                document.getElementById('growthChangeValue').textContent = formatScoreWithSign(change);
                document.getElementById('growthChangeValue').className = 'metric-value ' + (change >= 0 ? 'positive' : 'negative');
                
                document.getElementById('recommendationValue').textContent = formatScore(predictionData.recommendation_score);
                
                renderPredictionCharts(data.graphs, company);
            })
            .catch(error => {
                console.error('Error fetching prediction:', error);
                showNotification('Error', `Failed to load prediction data for ${company}.`, 'error');
                predictionDetails.classList.add('hidden');
            });
    }
    
    function renderPredictionCharts(graphsData, company) {
        Plotly.newPlot('growthComparisonChart', graphsData.growth_comparison.data, graphsData.growth_comparison.layout);
        Plotly.newPlot('recommendationGaugeChart', graphsData.recommendation_gauge.data, graphsData.recommendation_gauge.layout);
    }
    
    function formatScore(score) {
        return (score * 100).toFixed(2) + '%';
    }
    
    function formatScoreWithSign(score) {
        return (score >= 0 ? '+' : '') + (score * 100).toFixed(2) + '%';
    }
    
    companySelect.addEventListener('change', () => {
        const selectedCompany = companySelect.value;
        if (selectedCompany) {
            fetchCompanyPrediction(selectedCompany);
        } else {
            predictionDetails.classList.add('hidden');
        }
    });
    
    function loadRecommendations() {
        const theme = document.body.classList.contains('dark') ? 'dark' : 'light';
        console.log('Loading recommendations for theme:', theme);
        document.getElementById('topRecommendations').innerHTML = '<div class="loading">Loading recommendations...</div>';
        document.getElementById('bottomRecommendations').innerHTML = '<div class="loading">Loading recommendations...</div>';
        document.getElementById('combinedStocksChart').innerHTML = '';
        
        fetch(`/api/recommendations?theme=${theme}`)
            .then(response => response.json())
            .then(data => {
                console.log('Recommendations data:', data);
                document.getElementById('recommendationsContainer').style.display = 'block';
                document.getElementById('chatCard').classList.remove('full-width');
                renderRecommendationsList('topRecommendations', data.top_stocks, true);
                renderRecommendationsList('bottomRecommendations', data.bottom_stocks, false);
                if (data.graphs && data.graphs.combined_stocks) {
                    Plotly.newPlot('combinedStocksChart', data.graphs.combined_stocks.data, data.graphs.combined_stocks.layout);
                } else {
                    console.error('No graph data available for combined stocks');
                    document.getElementById('combinedStocksChart').innerHTML = '<div class="error">Failed to load recommendation graph</div>';
                }
            })
            .catch(error => {
                console.error('Error loading recommendations:', error);
                showNotification('Error', 'Failed to load stock recommendations.', 'error');
                document.getElementById('topRecommendations').innerHTML = '<div class="error">Failed to load recommendations</div>';
                document.getElementById('bottomRecommendations').innerHTML = '<div class="error">Failed to load recommendations</div>';
                document.getElementById('recommendationsContainer').style.display = 'block';
                document.getElementById('combinedStocksChart').innerHTML = '<div class="error">Failed to load recommendation graph</div>';
            });
    }
    
    function renderRecommendationsList(containerId, stocksData, isTop) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        if (!stocksData || stocksData.length === 0) {
            container.innerHTML = '<div class="no-data">No recommendation data available</div>';
            return;
        }
        
        const topCompanies = isTop ? stocksData.slice(0, 5) : stocksData.slice(-5).reverse();
        
        topCompanies.forEach(stock => {
            const company = stock.company || stock.ticker;
            const score = stock.recommendation_score || stock.weighted_score || 0;
            
            const item = document.createElement('div');
            item.className = `recommendation-item ${isTop ? 'good' : 'bad'}`;
            
            const companySpan = document.createElement('span');
            companySpan.className = 'company';
            companySpan.textContent = company;
            
            const scoreSpan = document.createElement('span');
            scoreSpan.className = 'score';
            scoreSpan.textContent = formatScore(score);
            
            item.appendChild(companySpan);
            item.appendChild(scoreSpan);
            
            item.addEventListener('click', () => {
                companySelect.value = company;
                const companySector = companiesData.find(c => c.ticker === company)?.sector || '';
                predictionSectorSelect.value = companySector;
                stockSectorSelect.value = companySector;
                updateCompanySelect(companySector);
                companySelect.dispatchEvent(new Event('change'));
                const predictionLink = document.querySelector('nav ul li a[href="#predictions"]');
                if (predictionLink) {
                    predictionLink.click();
                }
                showNotification('Info', `Viewing predictions for ${company}`, 'info');
            });
            
            container.appendChild(item);
        });
    }
    
    const runPredictionButton = document.getElementById('runPredictionButton');
    const predictionHorizon = document.getElementById('predictionHorizon');
    
    runPredictionButton.addEventListener('click', () => {
        const horizon = parseInt(predictionHorizon.value);
        
        runPredictionButton.disabled = true;
        runPredictionButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        
        showNotification('Processing', 'Running prediction model. This may take a minute...', 'info');
        
        fetch('/api/run_prediction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ horizon })
        })
        .then(response => response.json())
        .then(data => {
            runPredictionButton.disabled = false;
            runPredictionButton.innerHTML = 'Run Prediction';
            
            if (data.success) {
                showNotification('Success', data.message, 'success');
                hasPredictionRun = true;
                loadRecommendations();
                document.getElementById('lastPredictionDate').textContent = 'Last prediction: ' + new Date().toLocaleDateString();
            } else {
                showNotification('Error', data.error || 'Failed to run prediction.', 'error');
            }
        })
        .catch(error => {
            console.error('Error running prediction:', error);
            showNotification('Error', 'Failed to run prediction. Check server logs.', 'error');
            runPredictionButton.disabled = false;
            runPredictionButton.innerHTML = 'Run Prediction';
        });
    });
    
    const refreshButton = document.getElementById('refreshButton');
    refreshButton.addEventListener('click', () => {
        refreshButton.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
        
        if (hasPredictionRun) {
            loadRecommendations();
        }
        loadStocksTable(stockSectorSelect.value);
        
        setTimeout(() => {
            refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Data';
            showNotification('Refreshed', 'Data has been refreshed', 'success');
        }, 1000);
    });
    
    const stocksTableBody = document.getElementById('stocksTableBody');
    const stockSearch = document.getElementById('stockSearch');
    const searchButton = document.getElementById('searchButton');

    function loadStocksTable(sector = '') {
        console.log('Loading stocks for sector:', sector);
        stocksTableBody.innerHTML = '<tr><td colspan="7" class="loading">Loading stocks data...</td></tr>';
        
        const url = sector ? `/api/stock_table?sector=${encodeURIComponent(sector)}` : '/api/stock_table';
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('Stocks data:', data);
                stocksTableBody.innerHTML = '';
                
                if (!data.stocks || data.stocks.length === 0) {
                    stocksTableBody.innerHTML = '<tr><td colspan="7" class="error">No stock data available</td></tr>';
                    showNotification('Error', 'No stock data available.', 'error');
                    return;
                }
                
                data.stocks.forEach(stock => {
                    try {
                        const row = document.createElement('tr');
                        row.className = 'fade-in';
                        
                        const companyCell = document.createElement('td');
                        companyCell.textContent = stock.company || 'N/A';
                        row.appendChild(companyCell);
                        
                        const nameCell = document.createElement('td');
                        nameCell.textContent = stock.full_name || 'Unknown';
                        row.appendChild(nameCell);
                        
                        const ltpCell = document.createElement('td');
                        const ltp = parseFloat(stock.ltp || 0);
                        ltpCell.textContent = ltp > 0 ? `₹${ltp.toFixed(2)}` : 'N/A';
                        row.appendChild(ltpCell);
                        
                        const changeCell = document.createElement('td');
                        const changeDiv = document.createElement('div');
                        changeDiv.className = 'change-cell';
                        const changeValue = parseFloat(stock.change || 0);
                        changeDiv.innerHTML = `<i class="fas fa-${changeValue >= 0 ? 'arrow-up' : 'arrow-down'}"></i> ${changeValue.toFixed(2)}`;
                        changeCell.appendChild(changeDiv);
                        row.appendChild(changeCell);
                        
                        const growthCell = document.createElement('td');
                        const growthScore = parseFloat(stock.predicted_growth_score || 0);
                        console.log(`Raw predicted_growth_score for ${stock.company}: ${stock.predicted_growth_score}, parsed: ${growthScore}`);
                        growthCell.textContent = growthScore > 0 ? formatScore(growthScore) : 'N/A';
                        row.appendChild(growthCell);
                        
                        const recommendationCell = document.createElement('td');
                        const recommendationScore = parseFloat(stock.recommendation_score || 0);
                        if (recommendationScore > 0.66) {
                            recommendationCell.innerHTML = '<span class="badge success">Strong Buy</span>';
                        } else if (recommendationScore > 0.33) {
                            recommendationCell.innerHTML = '<span class="badge warning">Hold</span>';
                        } else {
                            recommendationCell.innerHTML = '<span class="badge danger">Sell</span>';
                        }
                        row.appendChild(recommendationCell);
                        
                        const actionCell = document.createElement('td');
                        const viewButton = document.createElement('button');
                        viewButton.className = 'action-button';
                        viewButton.textContent = 'View Details';
                        viewButton.addEventListener('click', () => {
                            companySelect.value = stock.company || '';
                            const companySector = companiesData.find(c => c.ticker === stock.company)?.sector || '';
                            predictionSectorSelect.value = companySector;
                            stockSectorSelect.value = companySector;
                            updateCompanySelect(companySector);
                            companySelect.dispatchEvent(new Event('change'));
                            const predictionLink = document.querySelector('nav ul li a[href="#predictions"]');
                            if (predictionLink) predictionLink.click();
                            showNotification(`Viewing predictions for ${stock.company}`, 'info');
                        });
                        actionCell.appendChild(viewButton);
                        row.appendChild(actionCell);
                        
                        stocksTableBody.appendChild(row);
                    } catch (error) {
                        console.error(`Error processing stock ${stock.company || 'unknown'}:`, error, stock);
                    }
                });
            })
            .catch(error => {
                console.error('Error loading stocks table:', error);
                stocksTableBody.innerHTML = '<tr><td colspan="7" class="error">Failed to load stocks data</td></tr>';
                showNotification('Error', 'Failed to load stocks table. Please try again.', 'error');
            });
    }
    
    function filterStocks() {
        const searchTerm = stockSearch.value.toLowerCase();
        const rows = stocksTableBody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const company = row.cells[0].textContent.toLowerCase();
            const fullName = row.cells[1].textContent.toLowerCase();
            
            if (company.includes(searchTerm) || fullName.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        showNotification('Info', 'Stocks filtered by search term.', 'info');
    }
    
    stockSearch.addEventListener('input', () => {
        filterStocks();
    });

    searchButton.addEventListener('click', () => {
        filterStocks();
    });

    // Sector Filter Event Listeners
    stockSectorSelect.addEventListener('change', () => {
        const selectedSector = stockSectorSelect.value;
        console.log('Stock sector changed:', selectedSector);
        predictionSectorSelect.value = selectedSector;
        updateCompanySelect(selectedSector);
        loadStocksTable(selectedSector);
        showNotification('Info', `Filtered stocks by ${selectedSector || 'all sectors'}`, 'info');
    });

    predictionSectorSelect.addEventListener('change', () => {
        const selectedSector = predictionSectorSelect.value;
        console.log('Prediction sector changed:', selectedSector);
        stockSectorSelect.value = selectedSector;
        updateCompanySelect(selectedSector);
        loadStocksTable(selectedSector);
        showNotification('Info', `Filtered companies by ${selectedSector || 'all sectors'}`, 'info');
    });
    
    // Notification system
    function showNotification(title, message, type) {
        console.log('Showing notification:', title, message, type);
        const notificationContainer = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <div class="notification-close">
                <i class="fas fa-times"></i>
            </div>
        `;
        
        notificationContainer.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.parentElement.removeChild(notification);
                }
            }, 300);
        }, 5000);
        
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.parentElement.removeChild(notification);
                }
            }, 300);
        });
    }
    
    // Initialize the page
    loadSectors();
    loadCompanies();
    loadStocksTable();
});