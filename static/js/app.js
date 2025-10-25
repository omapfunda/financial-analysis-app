// Financial Analysis Web App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add loading spinner to forms
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing...';
                submitBtn.disabled = true;
            }
        });
    });

    // Ticker input validation and formatting
    var tickerInputs = document.querySelectorAll('input[name="ticker"], input[name="tickers"]');
    tickerInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });

    // Preset screener buttons
    var presetButtons = document.querySelectorAll('.preset-btn');
    presetButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var preset = this.dataset.preset;
            applyPreset(preset);
        });
    });

    // Quick analysis buttons
    var quickAnalyzeButtons = document.querySelectorAll('.quick-analyze');
    quickAnalyzeButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var ticker = this.dataset.ticker;
            if (ticker) {
                window.location.href = '/analyze?ticker=' + ticker;
            }
        });
    });

    // Compare all button
    var compareAllBtn = document.getElementById('compare-all-btn');
    if (compareAllBtn) {
        compareAllBtn.addEventListener('click', function() {
            var checkboxes = document.querySelectorAll('.stock-checkbox:checked');
            var tickers = Array.from(checkboxes).map(cb => cb.value);
            if (tickers.length > 0) {
                window.location.href = '/compare?tickers=' + tickers.join(',');
            } else {
                alert('Please select at least one stock to compare.');
            }
        });
    }

    // Export to CSV functionality
    var exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportTableToCSV('screening-results-table', 'screening_results.csv');
        });
    }

    // Smooth scrolling for anchor links
    var anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add fade-in animation to cards
    var cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });

    // Dynamic progress bar animation
    var progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function(bar) {
        var width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = width;
            bar.style.transition = 'width 1s ease-in-out';
        }, 500);
    });
});

// Apply screener presets
function applyPreset(preset) {
    console.log('🔘 applyPreset called with preset:', preset);
    var form = document.getElementById('screenerForm');
    if (!form) {
        console.error('❌ Form with ID "screenerForm" not found!');
        return;
    }
    console.log('✅ Form found:', form);

    // Clear all inputs first
    var inputs = form.querySelectorAll('input, select');
    inputs.forEach(function(input) {
        if (input.type === 'number' || input.type === 'text') {
            input.value = '';
        } else if (input.type === 'select-one') {
            input.selectedIndex = 0;
        }
    });

    // Apply preset values
    console.log('📋 Applying preset values for:', preset);
    switch(preset) {
        case 'conservative':
            console.log('🛡️ Applying conservative preset...');
            // Market Cap: Large-cap companies (min $10B) for stability
            setFormValue('market_cap_min', '10000');
            setFormValue('pe_ratio_max', '20');
            setFormValue('debt_equity_max', '0.5');
            setFormValue('roe_min', '15');
            setFormValue('current_ratio_min', '1.5');
            setFormValue('dividend_yield_min', '2');
            setFormValue('min_pillars_score', '6');
            console.log('✅ Conservative preset applied');
            break;
        
        case 'growth':
            // Market Cap: Mid-to-large cap (min $2B) for growth potential
            setFormValue('market_cap_min', '2000');
            setFormValue('pe_ratio_max', '40');
            setFormValue('revenue_growth_min', '15');
            setFormValue('earnings_growth_min', '20');
            setFormValue('roe_min', '20');
            setFormValue('min_pillars_score', '5');
            break;
        
        case 'value':
            // Market Cap: All caps (min $500M) to include small-cap value opportunities
            setFormValue('market_cap_min', '500');
            setFormValue('pe_ratio_max', '15');
            setFormValue('price_book_max', '3');
            setFormValue('price_sales_max', '2');
            setFormValue('debt_equity_max', '0.6');
            setFormValue('min_pillars_score', '4');
            break;
    }
}

// Helper function to set form values
function setFormValue(name, value) {
    console.log(`   Setting ${name} = ${value}`);
    var input = document.querySelector(`input[name="${name}"], select[name="${name}"]`);
    if (input) {
        input.value = value;
        console.log(`   ✅ ${name} set to: ${input.value}`);
    } else {
        console.error(`   ❌ Field ${name} not found!`);
    }
}

// Reset form to default values
function resetForm() {
    console.log('🔄 resetForm called');
    var form = document.getElementById('screenerForm');
    if (!form) {
        console.error('❌ Form with ID "screenerForm" not found!');
        return;
    }
    console.log('✅ Form found for reset:', form);

    // Clear all inputs
    var inputs = form.querySelectorAll('input, select');
    inputs.forEach(function(input) {
        if (input.type === 'number' || input.type === 'text') {
            input.value = '';
        } else if (input.type === 'select-one') {
            input.selectedIndex = 0;
        }
    });

    // Set default values
    setFormValue('market_cap_min', '1000');
    setFormValue('pe_ratio_max', '25');
    setFormValue('debt_equity_max', '1.0');
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    var table = document.getElementById(tableId);
    if (!table) return;

    var csv = [];
    var rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        var cols = row.querySelectorAll('td, th');
        var csvRow = [];
        cols.forEach(function(col) {
            csvRow.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(csvRow.join(','));
    });

    downloadCSV(csv.join('\n'), filename);
}

// Download CSV file
function downloadCSV(csv, filename) {
    var csvFile = new Blob([csv], { type: 'text/csv' });
    var downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Format numbers for display
function formatNumber(num, decimals = 2) {
    if (isNaN(num)) return 'N/A';
    return parseFloat(num).toFixed(decimals);
}

// Format currency
function formatCurrency(num, decimals = 2) {
    if (isNaN(num)) return 'N/A';
    return '$' + parseFloat(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Format percentage
function formatPercentage(num, decimals = 1) {
    if (isNaN(num)) return 'N/A';
    return parseFloat(num).toFixed(decimals) + '%';
}

// Format large numbers (millions, billions)
function formatLargeNumber(num) {
    if (isNaN(num)) return 'N/A';
    
    var absNum = Math.abs(num);
    if (absNum >= 1e9) {
        return (num / 1e9).toFixed(1) + 'B';
    } else if (absNum >= 1e6) {
        return (num / 1e6).toFixed(1) + 'M';
    } else if (absNum >= 1e3) {
        return (num / 1e3).toFixed(1) + 'K';
    } else {
        return num.toFixed(0);
    }
}

// Show loading overlay
function showLoading() {
    var overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center">
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-3">
                    <h5>Analyzing financial data...</h5>
                    <p class="text-muted">This may take a few moments</p>
                </div>
            </div>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        z-index: 9999;
        display: flex;
    `;
    document.body.appendChild(overlay);
}

// Hide loading overlay
function hideLoading() {
    var overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Validate ticker symbol
function validateTicker(ticker) {
    var pattern = /^[A-Z]{1,5}$/;
    return pattern.test(ticker);
}

// Show success message
function showSuccess(message) {
    showAlert(message, 'success');
}

// Show error message
function showError(message) {
    showAlert(message, 'danger');
}

// Show warning message
function showWarning(message) {
    showAlert(message, 'warning');
}

// Show info message
function showInfo(message) {
    showAlert(message, 'info');
}

// Generic alert function
function showAlert(message, type) {
    var alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
        document.body.appendChild(alertContainer);
    }

    var alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    alertContainer.appendChild(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        if (alert.parentNode) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showSuccess('Copied to clipboard!');
    }, function() {
        showError('Failed to copy to clipboard');
    });
}

// Initialize charts with responsive options
function initializeChart(elementId, data, options = {}) {
    var element = document.getElementById(elementId);
    if (!element) return;

    var defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: options.title || 'Chart'
            }
        }
    };

    var config = {
        type: options.type || 'line',
        data: data,
        options: Object.assign(defaultOptions, options)
    };

    return new Chart(element, config);
}