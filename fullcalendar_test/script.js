$(document).ready(function() {

  // page is now ready, initialize the calendar...

  $('#calendar').fullCalendar({
      // put your options and callbacks here
      events: {
    	    url: 'http://abeweb.herokuapp.com/calendarRead',
    	    type: 'POST',
    	    data: {
    	        custom_attribute: 'acbd'
    	    },
    	    error: function() {
    	        alert('There was an error while fetching events!');
    	    }
      }
  })



});

function saveEventUpdate(event) {
    url = 'http://abeweb.herokuapp.com/calendarUpdate'

    // Create a copy of the event object
    data = $.extend({}, event);

    // Replace string date with timestamp (ms since epoch)
    data.start = data.start.valueOf();
    if(data.end != undefined){  data.end = event.end.valueOf(); }

    data.custom_attribute = 'abcd';

    var ret_id = '';
    var jqxhr = $.post( url, data, function(responseData) {
        // Executed on successful update to backend

        // Newly added event
        if(event.id == undefined)
        {
            // Get event ID from insert response
            obj = jQuery.parseJSON(responseData);
            ret_id  = obj.id;
            event.id = ret_id;

            // Render the event on the calendar
            $('#calendar').fullCalendar('renderEvent', event, true);
        }
    })
    .fail(function() {
        alert( "Error sending update AJAX" );
    })
}
