let selection_count = 0;

function select_this_card(list_item, card_id) {
    const $list_item = $(list_item);
    const $holder_b = $("ul.cards-holders.b");
    const $button_start = $("button#btn-start-session");
    let is_selected = parseInt($list_item.attr("is-selected"));
    let max_selection = parseInt($list_item.attr("max-selection"));

    if (selection_count >= 5)
        alert("5 cards maximum!");
    else if (is_selected > max_selection)
        alert("Insufficient quantity!")
    else {
        $.post("/api/select_this_card", { card_id: card_id, session_id: $("input[name='session_id']").val() }, function (data) {
            if (data.status == 1) {
                selection_count += 1;
                is_selected += 1;
                max_selection -= 1;
                $list_item.attr("is-selected", is_selected);
                $list_item.attr("max-selection", max_selection);
                $list_item.addClass("is-selected")
                $list_item.find('span.max-selection').text(max_selection);
                $holder_b.append(`<li onclick="unselect_this_card(this, ${card_id})">
                    <img src="${data.card.image}" />
                </li>`);

                $button_start.prop("disabled", selection_count != 5);
            } else {
                alert(data.message);
            }
        });
    }
};

function unselect_this_card(card_item, card_id) {
    const $card_item = $(card_item);
    const $list_item = $(`ul.card-selection li#${card_id}`);
    const $button_start = $("button#btn-start-session");
    let is_selected = parseInt($list_item.attr("is-selected"));
    let max_selection = parseInt($list_item.attr("max-selection"));

    $.post("/api/unselect_this_card", { card_id: card_id, session_id: $("input[name='session_id']").val() }, function (data) {
        if (data.status == 1) {
            selection_count -= 1;
            is_selected -= 1;
            max_selection += 1;
            $list_item.attr("is-selected", is_selected);
            $list_item.attr("max-selection", max_selection);
            $list_item.find('span.max-selection').text(max_selection);

            if (is_selected == 0)
                $list_item.removeClass("is-selected");

            $card_item.remove();
            $button_start.prop("disabled", true);
        } else {
            alert(data.message);
        }
    });
};

/**
 * Game 
 */
const $board = $("div#board");

function start_websocket(session_id) {
    let websocket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws?session_id=' + session_id);

    websocket.onopen = () => {
        console.log("Game start!");
    };
    websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);

        switch (message.action) {
            case "opp_prepare_to_move":
                break;
            case "opp_move_to_zone":
                break;
        };
    };
    websocket.onerror = () => { };
    websocket.onclose = () => { };

    return websocket;
}


function opp_prepare_to_move(hold_id) {
    $board.find(`ul.cards-holders.a li`).each((i, e) => {
        const $item = $(e);
        
        $item.attr("is-selected", "0").find("img").css({ marginLeft: 0 });

        if (parseInt($item.attr("hold-id")) == hold_id)
            $item.attr("is-selected", "1").find("img").css({ marginLeft: 15 });
    });
}


function opp_move_to_zone(cell_id) {
    $board.find(`ul.cards-holders.ab li div.card-image#${cell_id}[is-occupied="0"]`).each((i, e) => {
        const $target = $(e);

        $board.find("ul.cards-holders.a li[is-selected='1']").each((i, e) => {
            const $item = $(e);

            $target.html(
                $item.find("img").css({ marginLeft: 0 })
            );
            $target.attr("is-occupied", 1);
            $item.remove();
        });
    });
}

function next_action(side, message) {
    console.log(message);
    setTimeout(() => opp_prepare_to_move(1), 1000);
    setTimeout(() => opp_prepare_to_move(2), 3000);
    setTimeout(() => opp_prepare_to_move(1), 3500);

    setTimeout(() => opp_move_to_zone(3), 6000);
}

function prepare_to_move(target) {
    $board.find("ul.cards-holders.b li").each((i, e) => {
        $(e).attr("is-selected", "0").find("img").css({ marginLeft: 0 });

        if (e == target)
            $(e).attr("is-selected", "1").find("img").css({ marginLeft: -15 });
    });
}

function move_zone(target) {
    const $target = $(target);

    $board.find("ul.cards-holders.b li[is-selected='1']").each((i, e) => {
        const $item = $(e);

        if ($target.is(':empty')) {
            $target.html(
                $item.find("img").css({ marginLeft: 0 })
            );
            $target.attr("is-occupied", 1);
            $item.remove();

            return next_action("b", JSON.stringify({
                action: "move",
                arguments: {
                    cell_id: parseInt($target.attr("id")),
                    hand_id: parseInt($item.attr("hand-id")),
                    hold_id: parseInt($item.attr("hold-id")),
                }
            }));
        }
    });
}