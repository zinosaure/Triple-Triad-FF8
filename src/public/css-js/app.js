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