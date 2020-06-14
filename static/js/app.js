var suggestion_url = "/suggestions?term=";
var excel_file = "";
var results = [];
var table = null;

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
    document.getElementById('_iframe').href = "/" + excel_file;
    document.getElementById('_iframe').click();
}

// show detail of row
function show_detail(id){

    var html = "";

    $('#title').html(results[id]['heading_title']);
    $('#pubmed_link').html(results[id]['Pubmed link']);
    $('#date').html(results[id]['date']);
    $('#abstract').html(results[id]['abstract']);
    $('#authors').html(results[id]['authors_list']);
    $('#author_email').html(results[id]['author_email']);
    $('#author_affiliation').html(results[id]['affiliation']);
    $('#pmcid').html(results[id]['pmcid']);
    $('#doi').html(results[id]['doi']);
    $('#full_text_link').html(results[id]['full_text_links']);
    $('#mesh_terms').html(results[id]['mesh_terms']);
    $('#publication_type').html(results[id]['publication_types']);

    $('#modal').modal('show');
}


//truncate long text
function truncate(str, len=40) {
    /*
        truncate text

        @params:
                n: string,
                len: int
        @return:
                truncated string
    */

    if(str.length <= len) {
        return str;
    }

    var ext = str.substring(str.length - 3, str.length);
    var filename = str.replace(ext,'');

    return filename.substr(0, len-3) + (str.length > len ? '...' : '');
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
    var html = "";
    $('#table_div').empty();

    var table = '<table id="results_table" class="table table-striped table-bordered dt-responsive nowrap" style="width:100%"><thead><tr><th>_NO</th><th>Pubmed link</th><th>Title</th><th>Date</th><th>Abstract</th><th>Authors</th><th>Author email</th><th>Author affiliation</th><th>PMCID</th><th>DOI</th><th>Full text link</th><th>Mesh terms</th><th>Publication type</th></tr></thead><tbody></tbody>';
    $('#table_div').html(table);

    for ( var i = 0 ; i < results.length; i++ ){
        html += '<tr><td>' + (i+1) + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + results[i]["Pubmed link"] + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + results[i]["heading_title"] + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + results[i]["date"] + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + truncate(results[i]["abstract"]) + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + truncate(results[i]["authors_list"]) + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + truncate(results[i]["affiliation"]) + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + results[i]["author_email"] + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + results[i]["pmcid"] + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + results[i]["doi"] + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + truncate(results[i]["full_text_links"]) + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + truncate(results[i]["mesh_terms"]) + "</td>";
        html +='<td onclick="show_detail(' + i + ')">' + truncate(results[i]["publication_types"]) + "</td>";
        html += "</tr>";
    }

    $('#results_table tbody').html(html);
    $('#results_table').DataTable({});
}


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

    if (excel_file === "" || excel_file === null)
        $('#export_button').attr('disabled', true);
    else
        $('#export_button').attr('disabled', false);

    hide_spinner();
})