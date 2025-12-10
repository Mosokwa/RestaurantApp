// This script adds event listeners to handle sidebar toggle
document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.querySelector('.sidebar');
  const mainContent = document.querySelector('.main-content.with-sidebar');
  
  if (sidebar && mainContent) {
    // Add an observer to watch for class changes on sidebar
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'class') {
          if (sidebar.classList.contains('collapsed')) {
            mainContent.classList.add('collapsed-sidebar');
          } else {
            mainContent.classList.remove('collapsed-sidebar');
          }
        }
      });
    });
    
    observer.observe(sidebar, { attributes: true });
  }
});