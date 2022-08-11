(function () {
    "use strict";

    // Add CSRF token header for Ajax request
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", g.csrfToken);
            }
        }
    });

    // Flash message
    setTimeout(showFlash, 200);
    setTimeout(hideFlash, 5000);

    /**
     * Show flash message.
     */
    function showFlash() {
        $('.flash-message').slideDown('fast');
    }

    /**
     * Hide flash message.
     */
    function hideFlash() {
        $('.flash-message').slideUp('fast');
    }

})();


/* init burger menu */
(function() {
      var body = document.body;
      var burgerMenu = document.getElementsByClassName('b-menu')[0];
      var burgerContain = document.getElementsByClassName('b-container')[0];
      var burgerNav = document.getElementsByClassName('b-nav')[0];

      if (burgerMenu) {
        burgerMenu.addEventListener('click', function toggleClasses() {
                [body, burgerContain, burgerNav].forEach(function (el) {
                          el.classList.toggle('is-open');
                        });
              }, false);
      }
})();
