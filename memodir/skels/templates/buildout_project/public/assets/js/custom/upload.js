$(function(){

    unpack_zip_file_callback = function(file_name){
        setTimeout(function(){
            Dajaxice.upgrade.unpack_zip_file(Dajax.process, {'file_name': file_name});
        }, 2000)
    };


    recompile_project_callback = function(data){
        setTimeout(function(){
            Dajaxice.upgrade.recompile_project(Dajax.process);
        }, 2000)
    };


    restart_server_callback = function(data){
        setTimeout(function(){
            Dajaxice.upgrade.restart_server(Dajax.process);
        }, 2000)
    };

    upgrade_done_callback = function(data){
        Dajaxice.upgrade.upgrade_done(Dajax.process);
        //setTimeout(function(){}, 2000)
    };

    if ( $.browser.msie ) {
        $('#cool').removeClass('hide')
        $('#upload_submit_div').removeClass('hide')

    }

    else { // && $.browser.version >= '10.0') {
        $('#drop').removeClass('hide')

        var ul = $('#upload ul');

        $('#drop a').click(function(){
            // Simulate a click on the file input button
            // to show the file browser dialog
            $(this).parent().find('input').click();
        });

        // Initialize the jQuery File Upload plugin
        $('#upload').fileupload({

            // This element will accept file drag/drop uploading
            dropZone: $('#drop'),

            // This function is called when a file is added to the queue;
            // either via the browse button, or via drag/drop:
            add: function (e, data) {

                var tpl = $('<li class="working"><input type="text" value="0" data-width="48" data-height="48"'+
                    ' data-fgColor="#0788a5" data-readOnly="1" data-bgColor="#3e4043" />' +
                    '<p style="width:80%; margin:0;"></p><span></span></li>');

                file_name = data.files[0].name
                if (file_name.indexOf('.zip') > 0 || file_name.indexOf('.tar.gz') > 0) {
                    $('#error_msg').empty().addClass('hide');

                    // Append the file name and file size
                    tpl.find('p').text(data.files[0].name)
                                 .append('<i>' + formatFileSize(data.files[0].size) + '</i>');

                    // Add the HTML to the UL element
                    data.context = tpl.appendTo(ul);

                    // Initialize the knob plugin
                    tpl.find('input').knob();

                    // Listen for clicks on the cancel icon
                    tpl.find('span').click(function(){

                        if(tpl.hasClass('working')){
                            jqXHR.abort();
                        }

                        tpl.fadeOut(function(){
                            tpl.remove();
                        });

                    });

                    // Automatically upload the file once it is added to the queue
                    var jqXHR = data.submit();
                }
                else {
                    $('#error_msg').text('You can only upload .zip or .tar.gz upgrade patch file').removeClass('hide');
                }
            },

            progress: function(e, data){

                // Calculate the completion percentage of the upload
                var progress = parseInt(data.loaded / data.total * 100, 10);

                // Update the hidden input field and trigger a change
                // so that the jQuery knob plugin knows to update the dial
                data.context.find('input').val(progress).change();

                if(progress == 100){
                    data.context.removeClass('working');
                }
            },

            fail:function(e, data){
                // Something has gone wrong!
                data.context.addClass('error');
            },

            done: function(e, data){
                setTimeout(function(){

                    $('#drop').addClass('hide');
                    $('ul').addClass('hide');
                    $('#loader_div').removeClass('hide');
                    $('#msg_div').text('Uploading DONE, \n\n Upgrade Start ...');

                    setTimeout(function(){
                        $('#msg_div').text('Unpacking zip file ...');
                        file_name = data.files[0].name;
                        console.log(file_name);
                        unpack_zip_file_callback(file_name);
                    }, 1000)

                }, 1000);
            }

        });

        // Prevent the default action when a file is dropped on the window
        $(document).on('drop dragover', function (e) {
            e.preventDefault();
        });

        // Helper function that formats the file sizes
        function formatFileSize(bytes) {
            if (typeof bytes !== 'number') {
                return '';
            }

            if (bytes >= 1000000000) {
                return (bytes / 1000000000).toFixed(2) + ' GB';
            }

            if (bytes >= 1000000) {
                return (bytes / 1000000).toFixed(2) + ' MB';
            }

            return (bytes / 1000).toFixed(2) + ' KB';
        }
    }

});