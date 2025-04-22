/**
 * Library Management System
 * Main JavaScript file for interactive features
 * Sharda University - Enhanced Interactive Version
 */

$(document).ready(function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'hover',
            container: 'body'
        });
    });
    
    // Add animation classes with staggered delay
    $('.container > .row').each(function(index) {
        const $row = $(this);
        setTimeout(function() {
            $row.addClass('animate-fade-in');
        }, index * 150);
    });
    
    // Add ripple effect to buttons
    $('.btn').addClass('btn-ripple');
    
    // Active navigation highlighting with elegant transition
    const currentPath = window.location.pathname;
    $('.navbar-nav .nav-link').each(function() {
        const linkPath = $(this).attr('href');
        if (currentPath === linkPath || currentPath.startsWith(linkPath) && linkPath !== '/') {
            $(this).addClass('active');
            // Scroll to active menu item
            const $navItem = $(this).parent();
            const $navbarNav = $('.navbar-nav');
            if ($navbarNav.scrollLeft) {
                $navbarNav.animate({
                    scrollLeft: $navItem.offset().left - $navbarNav.offset().left
                }, 500);
            }
        }
    });
    
    // Enhanced date formatting
    $('.format-date').each(function() {
        const timestamp = $(this).text();
        if (timestamp && timestamp !== '-') {
            try {
                const date = new Date(timestamp);
                if (!isNaN(date)) {
                    const options = { 
                        weekday: 'short',
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    };
                    $(this).text(date.toLocaleDateString(undefined, options));
                    
                    // Add tooltip with time elapsed
                    const timeElapsed = getTimeElapsed(date);
                    $(this).attr('data-bs-toggle', 'tooltip');
                    $(this).attr('data-bs-placement', 'top');
                    $(this).attr('title', timeElapsed);
                    new bootstrap.Tooltip(this);
                }
            } catch (e) {
                console.error("Error formatting date:", e);
            }
        }
    });
    
    // Helper function to get time elapsed
    function getTimeElapsed(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        const diffMonth = Math.floor(diffDay / 30);
        const diffYear = Math.floor(diffMonth / 12);
        
        if (diffYear > 0) return diffYear + (diffYear === 1 ? ' year ago' : ' years ago');
        if (diffMonth > 0) return diffMonth + (diffMonth === 1 ? ' month ago' : ' months ago');
        if (diffDay > 0) return diffDay + (diffDay === 1 ? ' day ago' : ' days ago');
        if (diffHour > 0) return diffHour + (diffHour === 1 ? ' hour ago' : ' hours ago');
        if (diffMin > 0) return diffMin + (diffMin === 1 ? ' minute ago' : ' minutes ago');
        return 'Just now';
    }
    
    // Enhanced confirm dialogs with SweetAlert if available
    $('.confirm-delete').on('click', function(e) {
        e.preventDefault();
        const targetUrl = $(this).attr('href');
        const itemName = $(this).data('item-name') || 'this item';
        
        if (typeof Swal !== 'undefined') {
            // Use SweetAlert if available
            Swal.fire({
                title: 'Are you sure?',
                text: `You are about to delete ${itemName}. This action cannot be undone!`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Yes, delete it!',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = targetUrl;
                }
            });
        } else {
            // Fall back to standard confirm
            if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
                window.location.href = targetUrl;
            }
        }
    });
    
    // Enhanced return book confirmation
    $('.confirm-return').on('click', function(e) {
        e.preventDefault();
        const form = $(this).closest('form');
        const bookTitle = $(this).data('book-title') || 'this book';
        
        if (typeof Swal !== 'undefined') {
            // Use SweetAlert if available
            Swal.fire({
                title: 'Confirm Return',
                text: `Are you confirming that "${bookTitle}" is being returned?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#28a745',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Yes, confirm return',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
        } else {
            // Fall back to standard confirm
            if (confirm(`Confirm that "${bookTitle}" is being returned?`)) {
                form.submit();
            }
        }
    });
    
    // Enhanced overdue highlighting with animated warning
    $('.check-overdue').each(function() {
        const dueDate = new Date($(this).data('due-date'));
        const now = new Date();
        
        if (dueDate < now) {
            $(this).addClass('text-overdue');
            $(this).find('.badge').removeClass('bg-warning').addClass('bg-danger');
            
            // Add overdue indicator
            const daysDiff = Math.floor((now - dueDate) / (1000 * 60 * 60 * 24));
            $(this).find('td:last-child').prepend(
                `<span class="badge bg-danger me-2" data-bs-toggle="tooltip" title="${daysDiff} days overdue">
                    <i class="fas fa-exclamation-triangle"></i> Overdue
                </span>`
            );
            
            // Init tooltip on the new element
            new bootstrap.Tooltip($(this).find('[data-bs-toggle="tooltip"]')[0]);
        }
    });
    
    // Animated counters for statistics values
    $('.counter-value').each(function() {
        const $this = $(this);
        const countTo = parseInt($this.text());
        
        if (!isNaN(countTo) && countTo > 0) {
            $({ countNum: 0 }).animate({
                countNum: countTo
            }, {
                duration: 1000,
                easing: 'swing',
                step: function() {
                    $this.text(Math.floor(this.countNum));
                },
                complete: function() {
                    $this.text(this.countNum);
                }
            });
        }
    });
    
    // Animated progress bars
    $('.progress-bar').each(function() {
        const $this = $(this);
        const width = $this.data('width');
        
        $this.css('width', 0);
        $this.animate({
            width: width + '%'
        }, 1000);
    });
    
    // Search input focus with animation
    $('#search-focus').on('click', function() {
        $('#search-input').focus();
        $('#search-input').addClass('pulse-animation');
        setTimeout(function() {
            $('#search-input').removeClass('pulse-animation');
        }, 1000);
    });
    
    // Enhanced form validation with visual feedback
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        // Add input event listeners for real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
                
                // Check if all required fields are valid
                const isFormValid = Array.from(form.querySelectorAll('[required]')).every(el => el.checkValidity());
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = !isFormValid;
                    if (isFormValid) {
                        submitBtn.classList.add('btn-pulse');
                    } else {
                        submitBtn.classList.remove('btn-pulse');
                    }
                }
            });
        });
        
        // Form submission
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Highlight the first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Toggle password visibility with icon change
    $('.toggle-password').on('click', function() {
        const input = $($(this).attr('toggle'));
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            $(this).find('i').removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            $(this).find('i').removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
    
    // Auto-dismiss alerts with fade effect
    setTimeout(function() {
        $('.alert-dismissible').fadeOut('slow', function() {
            $(this).alert('close');
        });
    }, 5000);
    
    // Interactive tables with row highlighting and actions
    $('.interactive-table tbody tr').on('click', function(e) {
        if (!$(e.target).is('a, button, input')) {
            $('.interactive-table tbody tr').removeClass('table-active');
            $(this).addClass('table-active');
        }
    });
    
    // Add Sharda University branding watermark
    $('body').append('<div class="watermark">Sharda University Library</div>');
    
    // Dynamic year in copyright
    $('.copyright-year').text(new Date().getFullYear());
    
    // Add scroll-to-top button
    $('body').append('<button id="scroll-top" class="btn btn-primary rounded-circle position-fixed" style="bottom: 20px; right: 20px; display: none; z-index: 1000;"><i class="fas fa-arrow-up"></i></button>');
    
    // Show/hide scroll-to-top button based on scroll position
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            $('#scroll-top').fadeIn();
        } else {
            $('#scroll-top').fadeOut();
        }
    });
    
    // Smooth scroll to top when button clicked
    $('#scroll-top').on('click', function() {
        $('html, body').animate({ scrollTop: 0 }, 500);
        return false;
    });
    
    // Add CSS for watermark
    $('<style>')
        .text(
            '.watermark { position: fixed; bottom: 20px; left: 20px; opacity: 0.1; font-size: 16px; z-index: -1; transform: rotate(-45deg); transform-origin: bottom left; }'
        )
        .appendTo('head');
    
    // Add pulse animation for new elements
    $('<style>')
        .text(
            '@keyframes pulse-animation { 0% { box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(13, 110, 253, 0); } 100% { box-shadow: 0 0 0 0 rgba(13, 110, 253, 0); } } .pulse-animation { animation: pulse-animation 1.5s infinite; }'
        )
        .appendTo('head');
}); 