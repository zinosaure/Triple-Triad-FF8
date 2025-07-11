// Expects query param: ?game_id=...
const game_id = (new URLSearchParams(window.location.search)).get('game_id');
const websocket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws?game_id=' + game_id);
const $board = $("div#board");

websocket.onopen = () => {
    if (game_id == null)
        websocket.send(JSON.stringify({ "action": "setup" }));
    else
        websocket.send(JSON.stringify({ "action": "start-game" }));
};
websocket.onmessage = (event) => {
    const message = JSON.parse(event.data);

    console.log(message)


    if (message.game_id != "") {
        if (message.type == "reload") {
            window.location.href = `/?game_id=${message.game_id}`;
        } else if (message.type === "distribute") {
            const $hold_a = $board.find("ul.cards-holders.a");
            const $hold_b = $board.find("ul.cards-holders.b");
            const $hold_ab = $board.find("ul.cards-holders.ab");

            for (var i in message.board.hold.a)
                $hold_a.append(`<li>
                    <img 
                        cid="${message.board.hold.a[i].id}" 
                        pid="a" 
                        src="${message.board.hold.a[i].image}"
                    />
                </li>`);

            for (var i in message.board.hold.b)
                $hold_b.append(`<li is-selected="0" onclick="on_select(this)">
                    <img 
                        cid="${message.board.hold.b[i].id}" 
                        pid="b" 
                        src="${message.board.hold.b[i].image}"
                    />
                </li>`);

            for (var i = 0; i < 9; i++) {
                $hold_ab.append(`<li id="P${i}">
                    <div class="element"></div>
                    <div class="handicap"></div>
                    <div class="card-image" onclick="place_selected(this)">${((i) => {
                        if (typeof message.board.ondeck[i] !== 'undefined')
                            return `<img 
                                        cid="${message.board.ondeck[i].id}" 
                                        pid="${message.board.ondeck[i].pid}" 
                                        src="${message.board.ondeck[i].image}" 
                                    />`;
                        return '';
                    })(i)}</div>
                </li>`);
            }
        } else if (message.type === "error") {
        }
    }
};
websocket.onerror = () => {

};
websocket.onclose = () => {
};

function on_select(target) {
    $board.find(".cards-holders.b li").each((i, e) => {
        $(e).attr("is-selected", "0")
            .find("img")
            .css({ marginLeft: 0 });

        if (e == target)
            $(e).attr("is-selected", "1")
                .find("img")
                .css({ marginLeft: -15 });
    });
}

function place_selected(target) {
    const $target = $(target);

    $board.find(".cards-holders.b li[is-selected='1']").each((i, e) => {
        const $item = $(e);

        if ($target.is(':empty')) {
            $target
                .html(
                    $item
                        .find("img")
                        .css({ marginLeft: 0 })
                );
            $item.remove();
            return next_turn("a");
        }
    });
}

function next_turn(pid) {
    let placement = {};

    $board.find("ul.cards-holders.ab li .card-image").each((i, e) => {
        const $item = $(e);

        if ($item.is(':empty'))
            placement[`P${i}`] = null;
        else {
            const $image = $item.find("img");

            placement[`P${i}`] = {
                cid: $image.attr("cid"),
                pid: $image.attr("pid"),
            };
        }
    });

    websocket.send(JSON.stringify({ "action": `next_turn_${pid}`, "placement": placement }));
}