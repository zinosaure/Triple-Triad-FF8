let all_cards = {};
let selection_count = 0;
const session_id = (new URLSearchParams(window.location.search)).get('session_id');
const websocket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws?session_id=' + session_id);
const $board = $("div#board");
const $notification = $("div#notification");
const access_id = $('input[name="access_id"]').val();

if (session_id) {
    websocket.onopen = () => {
    };
    websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.access_id != access_id) {
            console.log(message)
            if (message.did == "JOINED_THE_GAME") {
                $notification.html("Has joined!");
            }

            if (message.did == "SELECTED_CARD" || message.did == "UNSELECTED_CARD") {
                const $ul = $board.find("ul.cards-holders.a");
                $ul.empty();

                for (var id in message.args) {
                    let card = all_cards[message.args[id]];

                    $ul.append(`<li id="${card.id}">
                        <img src="${card.image.a}" />
                    </li>`);
                }
            }
        }
    };
    websocket.onerror = () => { };
    websocket.onclose = () => {
        // window.location.reload();
    };
}

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
    else if (card_id in all_cards) {
        const card = all_cards[card_id];

        selection_count += 1;
        is_selected += 1;
        max_selection -= 1;
        $list_item.attr("is-selected", is_selected);
        $list_item.attr("max-selection", max_selection);
        $list_item.addClass("is-selected")
        $list_item.find('span.max-selection').text(max_selection);
        $holder_b.append(`<li onclick="unselect_this_card(this, ${card.id})">
            <img src="${card.image.b}" />
        </li>`);
        $button_start.prop("disabled", selection_count != 5);
        websocket.send(JSON.stringify({ type: "select_card", access_id: access_id, card_id: card_id, }));
    }
};

function unselect_this_card(card_item, card_id) {
    const $card_item = $(card_item);
    const $list_item = $(`ul.card-selection li#${card_id}`);
    const $button_start = $("button#btn-start-session");
    let access_id = $('input[name="access_id"]').val();
    let is_selected = parseInt($list_item.attr("is-selected"));
    let max_selection = parseInt($list_item.attr("max-selection"));

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
    websocket.send(JSON.stringify({ type: "unselect_card", access_id: access_id, card_id: card_id, }));
};

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
            $target.attr("is-occupied", PLAYRED);
            $item.remove();

            return capture_cells(PLAYRED, {});
        });
    });
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
            $target.attr("is-occupied", PLAYBLUE);
            $item.remove();

            return capture_cells(PLAYBLUE, JSON.stringify({
                action: "move",
                arguments: {
                    cell_id: parseInt($target.attr("id")),
                    hand_name: parseInt($item.attr("hand-id")),
                    hold_id: parseInt($item.attr("hold-id")),
                }
            }));
        }
    });
}

function capture_cells(hand_name, message) {
    if (hand_name == PLAYBLUE) {
        console.log(message);
        setTimeout(() => opp_prepare_to_move(1), 1000);
        setTimeout(() => opp_prepare_to_move(2), 3000);
        setTimeout(() => opp_prepare_to_move(1), 3500);

        setTimeout(() => opp_move_to_zone(3), 6000);
    } else {

    }
}


$(async (document) => {
    all_cards = await (await fetch("/public/images/cards/all.json")).json();
});