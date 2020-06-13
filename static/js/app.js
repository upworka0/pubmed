var suggestion_url = "/suggestions?term=";
var excel_file = "";
var results = [];

// Async Ajax Request
function AjaxRequest(url, method='GET', data=null){
    return new Promise((resolve, reject) => {
       $.ajax({
            url : url,
            method : method,
            data : data,
            success :  function(res){
                resolve(res);
            },
            error: function(err){
                reject();
            }
       });
    });
}

// show Spinner
function show_spinner(){
    $('#spinner').css('display', 'block');
}

// hide Spinner
function hide_spinner(){
    $('#spinner').css('display', 'none');
}


// Export excel file
function export_excel(){
    console.log("clicked!");
}

// show detail of row
function show_detail(id){
    $('#modal').modal('show');
}



/*$('#query').keypress(async function(eve){
    if (eve.keyCode == 32){
        var term = $('#query').val();
        var res = await AjaxRequest(suggestion_url + term);
        var data = JSON.parse(res);

        $('#query').typeahead('destroy');

        setTimeout(function(){
            $("#query").typeahead({ 
                source:data.suggestions
            });
        }, 200);
    }
})
*/

// Populate the table data
function populate_table(){
    $('#results_table tbody').html('');
}

populate_table();
// start scraping and show results in dataTable
$('#submit').click(async function(eve){
    var keyword = $('#query').val();
    if (keyword === ""){
        alert('Type search keyword please');
        return;
    }

    var data = {
        keyword: keyword
    };

    show_spinner();
    var res = await AjaxRequest('/scrap','POST',data);
    excel_file = res.excel_file;
    results = res.results;
    populate_table();    
    hide_spinner();
})