
function formatSectionMoney(section){
    $('#'+section).find('.money').each(function(){
        value = $(this).html()
        value = currency(value).format()
        $(this).html(String(value))
    })
}

function formatMoney(){

    $('.money').each(function(){
        value = $(this).html()
        value = currency(value).format()

        $(this).html(String(value))
    })
}
function pagination(per_page,page,data_length){

    if(per_page>data_length){
        var quo = 1;
    }else{
        var quo = Math.ceil(data_length/per_page);
    };


    var prev_page = parseInt(page)-1
    var previous_page = prev_page.toString()

    var meat = [];

    for(i=0;i<quo;i++){
        var numb = i+1;
        if(numb==page){
            var html = '<p class="pag active">'+numb+'</p>';
        }else{
            var html = '<p class="pag">'+numb+'</p>';
        };
        meat.push(html)
    };

    var pagination_html = meat.join('');

    var next_page = parseInt(page)+1
    var next_page = next_page.toString()

    var whole = data_length.toString();

    var start = 1+(page-1)*per_page;

    var end = page*per_page;
    if(end > data_length){
        var end = data_length;
    };

    var rows_html = 'Showing '+start+'-'+end+' of '+whole;

    return {'pagination_html':pagination_html,'rows_html':rows_html}

};
