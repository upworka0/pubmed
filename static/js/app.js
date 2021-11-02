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
                alert("Error was occurred!");
                hide_spinner();
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
    var ids = [
        "heading_title", "date", "abstract",
        "authors_list", "author_email", "affiliation",
        "pmcid", "doi", "mesh_terms",
        "publication_type"
    ];

    ids.forEach(function(ind, index){
        $('#' + ind).html(results[id][ind]);
    });

    $('#pubmed_link').html(results[id]['Pubmed link']);
    $('#pubmed_link').attr("href", results[id]['Pubmed link']);
    $('#author_email').attr("href", "mailto:" + results[id]['author_email']);

    $('#full_text_links').html(convert_full_text_links(results[id]['full_text_links']));

    $('#modal').modal('show');
}

// show detail of row
function show_clinical_detail(id){
    var html = "";
    var ids = [
        "nct_number", "conditions", "interventions", "outcome_measures",
        "heading_title", "date", "abstract",
        "authors_list", "author_email", "affiliation",
        "pmcid", "doi", "mesh_terms",
        "publication_type"
    ];

    ids.forEach(function(ind, index){
        $('#' + ind).html(results[id][ind]);
    });

    $('#pubmed_link').html(results[id]['Pubmed link']);
    $('#pubmed_link').attr("href", results[id]['Pubmed link']);
    $('#author_email').attr("href", "mailto:" + results[id]['author_email']);

    $('#full_text_links').html(convert_full_text_links(results[id]['full_text_links']));

    $('#modal').modal('show');
}

//truncate long text
function truncate(str, len=100) {
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

    return filename.substr(0, len-3) + (str.length > len ? '\n ......' : '');
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

function reformat_text(text){
    return text.split("\n").join("<br/>");
}


function convert_full_text_links(full_text_links){
    /* convert full text links to links with a tag */
    var tags = full_text_links.split('\n');
    var html = "";
    for ( var i = 0 ; i < tags.length; i++ ){
        html += '<a href="' + tags[i].replace(',','') + '" target="_blank">' + tags[i] + '</a><br/>';
    }

    return html;
}


// Populate the table data
function populate_table(){
    var html = "";
    $('#table_div').empty();

    var table = '<table id="results_table" class="table table-striped table-bordered dt-responsive nowrap" style="width:100%"><thead><tr><th>_NO</th><th>Pubmed link</th><th>Title</th><th>Date</th><th>Abstract</th><th>Authors</th><th>Author email</th><th>Author affiliation</th><th>PMCID</th><th>DOI</th><th>Full text link</th><th>Mesh terms</th><th>Publication type</th></tr></thead><tbody></tbody>';
    $('#table_div').html(table);

    for ( var i = 0 ; i < results.length; i++ ){
        html += '<tr><td>' + (i+1) + "</td>";
        html +='<td><div class="width-100"><a href="' + results[i]["Pubmed link"] + '" target="_blank">' + results[i]["Pubmed link"] + "</a></div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-220">' + truncate(results[i]["heading_title"], 150) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-80">' + results[i]["date"] + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-250">' + reformat_text(truncate(results[i]["abstract"], 250)) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["authors_list"])) + "</div></td>";
        html +='<td><div class="width-100"><a href="mailto:' + results[i]["author_email"] + '">' + results[i]["author_email"] + "</a></div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-200">' + reformat_text(truncate(results[i]["affiliation"], 200)) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-80">' + results[i]["pmcid"] + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-100">' + results[i]["doi"] + "</div></td>";
        html +='<td><div class="width-220">' + convert_full_text_links(results[i]["full_text_links"]) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["mesh_terms"])) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-100">' + reformat_text(results[i]["publication_types"]) + "</div></td>";
        html += "</tr>";
    }

    $('#results_table tbody').html(html);
    $('#results_table').DataTable({
        autoWidth: false, //step 1
        columnDefs: [
           { width: '300px', targets: 0 }, //step 2, column 1 out of 4
           { width: '300px', targets: 1 }, //step 2, column 2 out of 4
           { width: '300px', targets: 2 }  //step 2, column 3 out of 4
        ]
    });
}



// Populate the table data
function populate_clinical_table(){
    var html = "";
    $('#table_div').empty();

    var table = '<table id="results_table" class="table table-striped table-bordered dt-responsive nowrap" style="width:100%"><thead><tr><th>_NO</th><th>NCT number</th><th>Conditions</th><th>Interventions</th><th>Outcome measures</th><th>Pubmed link</th><th>Title</th><th>Date</th><th>Abstract</th><th>Authors</th><th>Author email</th><th>Author affiliation</th><th>PMCID</th><th>DOI</th><th>Full text link</th><th>Mesh terms</th><th>Publication type</th></tr></thead><tbody></tbody>';
    $('#table_clinical_div').html(table);

    for ( var i = 0 ; i < results.length; i++ ){
        html += '<tr><td>' + (i+1) + "</td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["nct_number"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["conditions"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["interventions"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["outcome_measures"], 150) + "</div></td>";
        html +='<td><div class="width-100"><a href="' + results[i]["Pubmed link"] + '" target="_blank">' + results[i]["Pubmed link"] + "</a></div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["heading_title"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-80">' + results[i]["date"] + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-250">' + reformat_text(truncate(results[i]["abstract"], 250)) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["authors_list"])) + "</div></td>";
        html +='<td><div class="width-100"><a href="mailto:' + results[i]["author_email"] + '">' + results[i]["author_email"] + "</a></div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-200">' + reformat_text(truncate(results[i]["affiliation"], 200)) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-80">' + results[i]["pmcid"] + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + results[i]["doi"] + "</div></td>";
        html +='<td><div class="width-220">' + convert_full_text_links(results[i]["full_text_links"]) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["mesh_terms"])) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + reformat_text(results[i]["publication_types"]) + "</div></td>";
        html += "</tr>";
    }

    $('#results_table tbody').html(html);
    $('#results_table').DataTable({
        autoWidth: false, //step 1
        columnDefs: [
           { width: '300px', targets: 0 }, //step 2, column 1 out of 4
           { width: '300px', targets: 1 }, //step 2, column 2 out of 4
           { width: '300px', targets: 2 }  //step 2, column 3 out of 4
        ]
    });
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
    $('#pdf_download').show();
    $('#extract_texts').show();
});

$('#clinical_submit').click(async function(eve){
    var conditions_disease = $('#conditions_disease').val();
    var other_terms = $('#other_terms').val();
    if (conditions_disease === "" && other_terms === ""){
        alert('Type search keyword please');
        return;
    }

    var data = {
        conditions_disease: conditions_disease,
        other_terms: other_terms
    };

    show_spinner();
    var res = await AjaxRequest('/clinical_scrap','POST',data);
    excel_file = res.excel_file;
    results = res.results;
    if (results.length === 0) {
        alert('No Result!')
    }
    populate_clinical_table();

    if (excel_file === "" || excel_file === null)
        $('#export_button').attr('disabled', true);
    else
        $('#export_button').attr('disabled', false);

    hide_spinner();
    $('#pdf_download').show();
    $('#extract_texts').show();
});

$('#pdf_download').click(async function(eve){
    show_spinner();
    await AjaxRequest('/download_pdf', 'GET');
    hide_spinner();
});

$('#extract_texts').click(async function(eve){
    show_spinner();
    await AjaxRequest('/extract_texts', 'GET');
    hide_spinner();
});