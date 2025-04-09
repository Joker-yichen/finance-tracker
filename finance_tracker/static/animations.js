/**
 * 财务记录系统页面动画和交互效果
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // 在页面加载时添加淡入效果（移除此功能，防止内容闪烁）
    // document.body.classList.add('loaded');
    
    // 数字增长动画
    if (document.querySelector('.overview-item')) {
        animateNumbers();
    }
    
    // 为按钮添加涟漪效果
    setupRippleEffect();
    
    // 为表单提交添加加载动画
    setupFormLoading();
    
    // 交易记录行的滑入动画
    if (document.querySelector('.table tbody tr')) {
        animateTransactionRows();
    }
    
    // 卡片懒加载动画
    animateCardsOnScroll();
});

/**
 * 数字增长动画 - 让金额数字从0增长到实际值
 */
function animateNumbers() {
    const numberElements = document.querySelectorAll('.overview-item .text-success, .overview-item .text-danger');
    
    numberElements.forEach(function(element) {
        const finalValue = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
        const prefix = element.textContent.replace(/[\d.-]/g, '');
        
        if (!isNaN(finalValue)) {
            let startValue = 0;
            const duration = 1500; // 动画持续时间（毫秒）
            const frameDuration = 16; // 每帧时间（毫秒）
            const totalFrames = Math.round(duration / frameDuration);
            const valueIncrement = finalValue / totalFrames;
            
            let currentFrame = 0;
            
            const animateValue = function() {
                currentFrame++;
                startValue += valueIncrement;
                
                element.textContent = `${prefix}${startValue.toFixed(2)}`;
                
                if (currentFrame < totalFrames) {
                    requestAnimationFrame(animateValue);
                } else {
                    element.textContent = `${prefix}${finalValue.toFixed(2)}`;
                }
            };
            
            requestAnimationFrame(animateValue);
        }
    });
}

/**
 * 为按钮添加涟漪效果
 */
function setupRippleEffect() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            this.appendChild(ripple);
            
            setTimeout(function() {
                ripple.remove();
            }, 600);
        });
    });
}

/**
 * 为表单提交添加加载动画
 */
function setupFormLoading() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            
            if (submitButton && !submitButton.classList.contains('loading-btn')) {
                const originalText = submitButton.textContent;
                submitButton.classList.add('loading-btn');
                
                // 保存原始文本并显示加载文本
                submitButton.setAttribute('data-original-text', originalText);
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
                
                // 提交后恢复按钮状态
                setTimeout(function() {
                    if (submitButton.classList.contains('loading-btn')) {
                        submitButton.classList.remove('loading-btn');
                        submitButton.innerHTML = originalText;
                    }
                }, 3000); // 3秒后恢复，避免服务器响应慢时按钮一直显示加载
            }
        });
    });
}

/**
 * 交易记录行的滑入动画
 */
function animateTransactionRows() {
    const tableRows = document.querySelectorAll('.table tbody tr');
    
    tableRows.forEach(function(row, index) {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(function() {
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, 100 + (index * 50)); // 错开时间，实现连续滑入效果
    });
}

/**
 * 卡片懒加载动画 - 滚动时显示卡片
 */
function animateCardsOnScroll() {
    const cards = document.querySelectorAll('.card');
    
    // 检查元素是否在可视区域内
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // 初始状态
    cards.forEach(function(card) {
        if (!isElementInViewport(card)) {
            card.classList.add('out-of-view');
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
        }
    });
    
    // 滚动时检查并显示卡片
    function handleScroll() {
        cards.forEach(function(card) {
            if (isElementInViewport(card) && card.classList.contains('out-of-view')) {
                card.classList.remove('out-of-view');
                card.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    }
    
    // 首次检查
    handleScroll();
    
    // 滚动时检查
    window.addEventListener('scroll', handleScroll);
}

/**
 * 切换明暗主题（备用功能）
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
} 