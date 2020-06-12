var suggestion_url = "/suggestions?term=";

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

$(document).ready(function(){

	$('#query').keypress(async function(eve){
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

    $('#submit').click(async function(eve){
        var keyword = $('#query').val();
        var data = {
            keyword: keyword
        };

        var res = await AjaxRequest('/scrap','POST',data);
        console.log(res);
    })

})