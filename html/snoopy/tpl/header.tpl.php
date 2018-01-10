<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8" />
	<title>MPD Webinterface</title>	

	<script type="text/javascript">
		var VOLDOWNSTEPS = <?php echo $volDownSteps?>;
		var VOLUPSTEPS = <? echo $volUpSteps?>;
	</script>
	
	<script type="text/javascript" src="media/jquery.js"></script>
	<script type="text/javascript" src="media/mycode.js?<?php echo filemtime("media/mycode.js");?>"></script>
	<link rel="stylesheet" type="text/css" href="media/style.css?<?php echo filemtime("media/style.css");?>" />
</head>
<body>

<div class="container">
	<div class="meta">
		<p>mpd <?php echo $mpd->mpd_version?></p>
	</div>
	<div class="navi">
		<ul>
			<li><a href="?a=voldown" id="volDown" title="Vol down"><img src="media/icons/sound_down.png" alt="Vol down" /></a></li>
			<li><a href="?a=volup" id="volUp" title="Vol up"><img src="media/icons/sound_up.png" alt="Vol up" /></a></li>
			<li><a href="?a=prev" id="prev" title="Previous"><img src="media/icons/control_rewind.png" alt="Previous" /></a></li>
			<?php if($mpd->state == 'pause' || $mpd->state == 'stop'): ?>
			<li><a href="?a=play" id="play" title="Play"><img src="media/icons/control_play.png" alt="Play" /></a></li>
			<?php else: ?>
			<li><a href="?a=pause" id="pause" title="Pause"><img src="media/icons/control_pause.png" alt="Pause" /></a></li>
			<?php endif; ?>
			<li><a href="?a=stop" id="stop" title="Stop"><img src="media/icons/control_stop.png" alt="Stop" /></a></li>
			<li><a href="?a=next" id="next" title="Next"><img src="media/icons/control_fastforward.png" alt="Fastforward" /></a></li>
		</ul>
	</div>


