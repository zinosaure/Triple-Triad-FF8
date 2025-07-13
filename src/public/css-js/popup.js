const popup = {
    init: function () {
        const $this = this;

        $(document).ready(function () {
            $this.spin = $('<h1 class="text-center"><i class="fa-solid fa-spinner fa-spin"></i></h1>').css({
                paddingTop: 24,
            });
            $this.content_child = $('<div class="card-body"></div>').append($this.spin);
            $this.content = $('<div class="card"></div>').css({
                width: 100,
                height: 100,
                minWidth: 50,
                maxWidth: '90vw',
                maxHeight: '90vh',
                overflowY: 'auto',
            }).append($this.content_child);
            $this.button_close = $('<a href="javascript:void(0)" onclick="return popup.close();">&times;</button>').css({
                zIndex: 9999,
                position: 'fixed',
                right: 25,
                top: 10,
                color: '#ffffff',
                fontSize: 40,
                textShadow: '0 0 15px #acacac',
                textDecoration: 'none',
            });
            $this.popup_child = $('<div />').css({
                zIndex: 9999,
                position: 'fixed',
                left: '50%',
                top: '50%',
                webkitTransform: 'translate(-50%, -50%)',
                transform: 'translate(-50%, -50%)',
                maxWidth: '90vw',
                maxHeight: '90vh',
                overflowY: 'auto',
            }).append($this.content);
            $this.popup = $('<div />').css({
                zIndex: 9998,
                display: 'none',
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100vw',
                height: '100vh',
                background: 'rgba(12, 12, 12, 0.80)',
                margin: 0,
                padding: 0,
            })
                .append($this.button_close)
                .append($this.popup_child)
                .prependTo('body');
        });

        return $this;
    },
    alert: function (html, button_text, width) {

    },
    confirm: function (html, button_text, width) {

    },
    open: function (html, width, permanent) {
        const $this = this;
        const $temp_html = $('<div style="display: none"></div>').html(html).appendTo('body');

        if (permanent || false)
            $this.button_close.hide();
        else
            $this.button_close.show();

        $this.popup.fadeIn(500, function () {
            let border = $this.content.css('border-width').replace('px', '') * 2;
            let padding = $this.content_child.css('padding-top').replace('px', '') * 2;

            $this.content_child.html(null);
            $this.content.animate({ width: width || '90vw', height: $temp_html.outerHeight() + padding + border }, function () {
                $this.content_child.append($temp_html.detach().show());
            });
        });
    },
    close: function () {
        const $this = this;

        $this.content_child.html(null);
        $this.content.animate({ width: 100, height: 100 }, function () {
            $this.content_child.html($this.spin);
            $this.popup.fadeOut(500);

        });
    },
}.init();
