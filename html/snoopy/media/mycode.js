$(document).ready(function() {
	/*
	
	TODO: 	Have to edit some more things to make that stuff working right
			well, you can uncomment it, but you have to refresh the page by hand ... sorry
	
	$("#next").click(function() {
		$.ajax({
			url: "index.php?a=next"
		});
		event.preventDefault();

		$("#outNext").fadeIn('slow', function() {
			$("#outNext").fadeOut('slow');
		});
	});

	$("#prev").click(function() {
		$.ajax({
			url: "index.php?a=prev"
		});
		event.preventDefault();

		$("#outPrev").fadeIn('slow', function() {
			$("#outPrev").fadeOut('slow');
		});
    });

	$("#play").click(function() {
		$.ajax({
		    url: "index.php?a=play"
		});
		event.preventDefault();

		$("#outPlay").fadeIn('slow', function() {
		    $("#outPlay").fadeOut('slow');
		});
	});

    $("#stop").click(function() {
		$.ajax({
			url: "index.php?a=stop"
		});
		event.preventDefault();

		$("#outStop").fadeIn('slow', function() {
			$("#outStop").fadeOut('slow');
		});
    });

    $("#pause").click(function() {
		$.ajax({
			url: "index.php?a=pause"
		});
		event.preventDefault();

		$("#outPause").fadeIn('slow', function() {
			$("#outPause").fadeOut('slow');
		});
	});
	*/

	$("#volUp").click(function(event) {
		$.ajax({
			url: "index.php?a=volup"
		});
		event.preventDefault();

		$("#outVolup").fadeIn('slow', function() {
			$("#outVolup").fadeOut('slow');
		});
		
		var currentvol = parseInt($("#currentvol").text());
		$("#currentvol").text(currentvol + VOLUPSTEPS);

	});

	$("#volDown").click(function(event) {
		$.ajax({
			url: "index.php?a=voldown"
		});
		event.preventDefault();

		$("#outVoldown").fadeIn('slow', function() {
			$("#outVoldown").fadeOut('slow');
		});
		
		var currentvol = parseInt($("#currentvol").text());
		$("#currentvol").text(currentvol - VOLDOWNSTEPS);
	});
 });

