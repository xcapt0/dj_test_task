let table = $('#table').DataTable({'order': []});
$(window).on('DOMContentLoaded', updateTable)

function updateTable() {
    let url = window.location.href
    url += `&page=0`

    $.get(url, function(data){
        if (data.total) {
            for (let page = 1; page < data.total; page++) {
                url = window.location.href

                $.get(url, {page: page}, function(table_data) {
                    if (table_data.status === 200) {
                        table.rows.add(table_data.table.values);
                        table.draw(false);
                    }
                });
            }
        }
    });
}