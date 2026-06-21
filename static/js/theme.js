document.addEventListener('DOMContentLoaded', function(){
    const savedTheme = localStorage.getItem('theme');

    if(savedTheme === 'light'){
        document.body.classList.add('light-theme');
    }else{
        document.body.classList.add('dark-theme');
    }

    const button = document.createElement('button');
    button.className = 'theme-toggle';

    function updateButtonText(){
        button.textContent = document.body.classList.contains('dark-theme')
            ? '\u0421\u0432\u0456\u0442\u043b\u0430'
            : '\u0422\u0435\u043c\u043d\u0430';
    }

    button.onclick = function(){
        if(document.body.classList.contains('dark-theme')){
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        }else{
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        }

        updateButtonText();
    };

    updateButtonText();
    document.body.appendChild(button);
});
