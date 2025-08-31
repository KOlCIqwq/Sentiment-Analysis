document.addEventListener('DOMContentLoaded', () => {
    // Dashboard state
    let currentDate = new Date();
    let confidenceThreshold = 0;
    let autoRefreshIntervalId = null;
    let debounceTimeout = null;

    // DOM elements
    const dateTitle = document.getElementById('date-title');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const clockElement = document.getElementById('clock');
    const articlesTbody = document.getElementById('articles-tbody');
    const confidenceSlider = document.getElementById('confidence-slider');
    const confidenceInput = document.getElementById('confidence-input');
    const sliderFill = document.querySelector('.slider-fill');
    const dailySummaryTitle = document.getElementById('daily-summary-title');
    const dailyPositive = document.getElementById('daily-positive');
    const dailyNegative = document.getElementById('daily-negative');
    const dailyNeutral = document.getElementById('daily-neutral');
    const monthlyPositive = document.getElementById('monthly-positive');
    const monthlyNegative = document.getElementById('monthly-negative');
    const monthlyTotal = document.getElementById('monthly-total');
    const backgroundGradient = document.querySelector('.background-gradient');

    // Utility functions
    const isSameDay = (d1, d2) => d1.getFullYear() === d2.getFullYear() && d1.getMonth() === d2.getMonth() && d1.getDate() === d2.getDate();
    const toYYYYMMDD = (date) => date.toISOString().split('T')[0];

    // Interactive gradient background
    function initializeGradientBackground() {
        let mouseX = 50;
        let mouseY = 50;
        let targetX = 50;
        let targetY = 50;

        document.addEventListener('mousemove', (e) => {
            targetX = (e.clientX / window.innerWidth) * 100;
            targetY = (e.clientY / window.innerHeight) * 100;
        });

        // Smooth animation for gradient movement
        function animateGradient() {
            const ease = 0.05;
            mouseX += (targetX - mouseX) * ease;
            mouseY += (targetY - mouseY) * ease;

            backgroundGradient.style.setProperty('--mouse-x', `${mouseX}%`);
            backgroundGradient.style.setProperty('--mouse-y', `${mouseY}%`);

            requestAnimationFrame(animateGradient);
        }
        
        animateGradient();
    }

    // Slider functionality
    function updateSliderFill() {
        const percentage = (confidenceThreshold / 100) * 100;
        sliderFill.style.width = `${percentage}%`;
    }

    function animateNumber(element, newValue, prefix = '') {
        element.style.animation = 'none';
        element.offsetHeight; // Trigger reflow
        element.style.animation = 'countUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) both';
        setTimeout(() => {
            element.textContent = prefix + newValue;
        }, 100);
    }

    function updateClock() {
        clockElement.textContent = new Date().toLocaleTimeString('en-GB');
    }

    function updateUIState() {
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);
        
        if (isSameDay(currentDate, today)) {
            dateTitle.textContent = "Today";
            dailySummaryTitle.textContent = "Today's Summary";
        } else if (isSameDay(currentDate, yesterday)) {
            dateTitle.textContent = "Yesterday";
            dailySummaryTitle.textContent = "Yesterday's Summary";
        } else {
            const dateString = currentDate.toLocaleDateString(undefined, { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            dateTitle.textContent = dateString;
            dailySummaryTitle.textContent = "Daily Summary";
        }
        
        btnNext.disabled = currentDate >= new Date().setHours(0, 0, 0, 0);
    }
    
    async function updateDashboard(showLoading = true) {
        if (isSameDay(currentDate, new Date())) startAutoRefresh();
        else stopAutoRefresh();

        const dateStr = toYYYYMMDD(currentDate);
        const confidence = confidenceThreshold / 100;
        const summaryParams = `?date=${dateStr}&confidence=${confidence}`;
        const articlesParams = `?date=${dateStr}&confidence=${confidence}`;
        
        if (showLoading) articlesTbody.classList.add('loading');
        updateUIState();

        try {
            const [summaryData, articlesData] = await Promise.all([
                fetch(`/api/summary${summaryParams}`).then(res => res.json()),
                fetch(`/api/articles${articlesParams}`).then(res => res.json())
            ]);
            
            const dailyPos = summaryData.daily.positive || 0;
            const dailyNeg = summaryData.daily.negative || 0;
            const dailyNeu = summaryData.daily.neutral || 0;
            const monthlyPos = summaryData.monthly.positive || 0;
            const monthlyNeg = summaryData.monthly.negative || 0;

            animateNumber(dailyPositive, dailyPos, '+');
            animateNumber(dailyNegative, dailyNeg, '-');
            animateNumber(dailyNeutral, dailyNeu, '~');
            animateNumber(monthlyPositive, monthlyPos, '+');
            animateNumber(monthlyNegative, monthlyNeg, '-');
            monthlyTotal.textContent = `Total: ${monthlyPos + monthlyNeg}`;

            setTimeout(() => {
                articlesTbody.innerHTML = '';
                if (articlesData.length > 0) {
                    articlesData.forEach((article, index) => {
                        const confidencePercent = (article.confidence * 100).toFixed(2);
                        const row = document.createElement('tr');
                        row.style.animationDelay = `${index * 0.05}s`;
                        row.innerHTML = `
                            <td data-label="Brief">${article.content}</td>
                            <td data-label="Company">${article.company || 'N/A'}</td>
                            <td data-label="Sentiment"><span class="sentiment ${article.sentiment}">${article.sentiment}</span></td>
                            <td data-label="Confidence">${confidencePercent}%</td>
                            <td data-label="Published">${article.time}</td>`;
                        articlesTbody.appendChild(row);
                    });
                } else {
                    const emptyRow = document.createElement('tr');
                    emptyRow.innerHTML = `<td colspan="5" style="text-align: center; padding: 2rem; color: #64748b; font-style: italic;">No processed articles found with the selected criteria.</td>`;
                    articlesTbody.appendChild(emptyRow);
                }
                articlesTbody.classList.remove('loading');
            }, 300);

        } catch (error) {
            console.error('Error fetching data:', error);
            articlesTbody.classList.remove('loading');
            articlesTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #ef4444;">Error loading data. Please try again.</td></tr>`;
        }
    }

    function stopAutoRefresh() { 
        if (autoRefreshIntervalId) {
            clearInterval(autoRefreshIntervalId);
            autoRefreshIntervalId = null;
        }
    }

    function startAutoRefresh() {
        stopAutoRefresh();
        autoRefreshIntervalId = setInterval(() => updateDashboard(false), 30000);
    }
    
    function handleConfidenceChange() {
        clearTimeout(debounceTimeout);
        updateSliderFill();
        debounceTimeout = setTimeout(() => {
            updateDashboard();
        }, 1000);
    }

    // Event listeners
    btnPrev.addEventListener('click', () => { 
        currentDate.setDate(currentDate.getDate() - 1); 
        updateDashboard(); 
    });
    
    btnNext.addEventListener('click', () => { 
        currentDate.setDate(currentDate.getDate() + 1); 
        updateDashboard(); 
    });
    
    confidenceSlider.addEventListener('input', (e) => {
        confidenceThreshold = parseInt(e.target.value, 10);
        confidenceInput.value = confidenceThreshold;
        handleConfidenceChange();
    });

    confidenceInput.addEventListener('input', (e) => {
        let value = parseInt(e.target.value, 10);
        if (isNaN(value) || value < 0) value = 0;
        if (value > 100) value = 100;
        confidenceThreshold = value;
        confidenceSlider.value = confidenceThreshold;
        e.target.value = confidenceThreshold;
        handleConfidenceChange();
    });

    // Prevent form submission on Enter key
    confidenceInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            confidenceInput.blur();
        }
    });

    // Add smooth scroll behavior for table
    function addScrollBehavior() {
        const table = document.querySelector('table');
        if (table) {
            table.addEventListener('wheel', (e) => {
                const delta = e.deltaY;
                const scrollTop = table.scrollTop;
                const maxScroll = table.scrollHeight - table.clientHeight;
                
                if ((delta > 0 && scrollTop >= maxScroll) || (delta < 0 && scrollTop <= 0)) {
                    return;
                }
                
                e.preventDefault();
                table.scrollTop += delta;
            }, { passive: false });
        }
    }

    // Add keyboard navigation
    function addKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return; // Don't interfere with input fields
            
            switch(e.key) {
                case 'ArrowLeft':
                    if (!btnPrev.disabled) {
                        btnPrev.click();
                        e.preventDefault();
                    }
                    break;
                case 'ArrowRight':
                    if (!btnNext.disabled) {
                        btnNext.click();
                        e.preventDefault();
                    }
                    break;
                case 'r':
                case 'R':
                    if (e.ctrlKey || e.metaKey) return; // Don't interfere with browser refresh
                    updateDashboard();
                    e.preventDefault();
                    break;
            }
        });
    }

    // Performance optimization - throttle resize events
    function addResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                // Trigger any resize-dependent calculations
                updateSliderFill();
            }, 250);
        });
    }

    // Add loading states for buttons
    function addButtonLoadingStates() {
        [btnPrev, btnNext].forEach(button => {
            button.addEventListener('click', () => {
                button.style.opacity = '0.6';
                button.style.pointerEvents = 'none';
                
                setTimeout(() => {
                    button.style.opacity = '';
                    button.style.pointerEvents = '';
                }, 1000);
            });
        });
    }

    // Initialize everything
    function initialize() {
        initializeGradientBackground();
        updateSliderFill();
        addScrollBehavior();
        addKeyboardNavigation();
        addResizeHandler();
        addButtonLoadingStates();
        
        // Start clock
        updateClock();
        setInterval(updateClock, 1000);
        
        // Load initial data
        updateDashboard();

        // Add some visual feedback for successful initialization
        setTimeout(() => {
            document.body.style.opacity = '1';
            document.body.style.transform = 'translateY(0)';
        }, 100);
    }

    // Set initial opacity and transform for smooth entrance
    document.body.style.opacity = '0';
    document.body.style.transform = 'translateY(20px)';
    document.body.style.transition = 'opacity 0.8s ease, transform 0.8s ease';

    // Initialize the dashboard
    initialize();

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        stopAutoRefresh();
    });
});