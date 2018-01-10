<?php if($status != 'stopped'): ?>
<?php if($status != 'paused'): ?>
<script type="text/javascript">
	var min = <?php echo date('i',$times[0])?>;
	var sec = <?php echo date('s',$times[0])?>;
	function zeropad(n, digits) { n = n.toString(); while (n.length < digits) { n = '0' + n; } return n; }
	function cnt() { sec++; if(sec > 59) { min++; sec = 0; } document.getElementById('time').innerHTML = zeropad(min,2) + ":" + zeropad(sec,2); }
	window.setInterval(cnt, 1000);
</script>
<?php endif; ?>
<p><span class="label">Current:</span><?php echo CURRENTARTIST ?> - <?php echo CURRENTTRACK?> (<span id="time"><? if($status == 'paused') { echo $CURRENTTIME[0].':'.$CURRENTTIME[1].':'.$CURRENTTIME[2];} ?></span><noscript><?php echo $CURRENTTIME[0].':'.$CURRENTTIME[1].':'.$CURRENTTIME[2];?></noscript><?php if($CURRENTLENGTH[0] + $CURRENTLENGTH[1] + $CURRENTLENGTH[2] > 0): ?>/<?php echo $CURRENTLENGTH[0] . ':' . $CURRENTLENGTH[1] . ':' . $CURRENTLENGTH[2]; ?><?php endif; ?>)</p>
<?php endif; ?>

<div class="playlist">
<?php foreach($mpd->playlist as $song) { ?>
	<?php if($song['Artist'] != NULL && $song['Title'] != NULL) { ?>
		<?php $sngtm = convertSecs($song['Time']); $songtime = ($sngtm[0] ? $sngtm[0].':' : '').$sngtm[1].':'.$sngtm[2]; ?>
		<?php if((CURRENTID-5) == $song['Id']) { ?> 
		
		<p>
			<a href="?a=remove&amp;id=<?php echo $song['Id']?>" title="Remove this song" class="removeid">x</a>
			<a href="?a=start&amp;id=<?php echo $song['Pos']?>" name="current">
				<?php echo $song['Artist']?> - <?php echo $song['Title']?> <span class="label">(<?php echo $songtime?>)</span> 
			</a>
		</p>

		<?php } elseif(CURRENTID == $song['Id']) { ?>

		<p class="current songLine">
            <span class="marker">&nbsp;</span>
		    <a href="?a=remove&amp;id=<?php echo $song['Id']?>" title="Remove this song" class="removeid">x</a>
			<a href="?a=start&amp;id=<?php echo $song['Pos']?>">
				<?php echo $song['Artist']?> - <?php echo $song['Title']?> <span class="label">(<?php echo $songtime?>)</span>
			</a>
		</p>	

		<?php } else { ?>

		<p class="songLine">
			<a href="?a=remove&amp;id=<?php echo $song['Id']?>" title="Remove this song" class="removeid">x</a>
			<a href="?a=start&amp;id=<?php echo $song['Pos']?>">
				<?php echo $song['Artist']?> - <?php echo $song['Title']?> <span class="label">(<?php echo $songtime?>)</span>
			</a>
		</p>

		<?php } ?>
	<?php } elseif($song['Name'] != NULL) { ?>
		<p class="songLine">
			<a href="?a=remove&amp;id=<?php echo $song['Id']?>" title="Remove this song" class="removeid">x</a>
			<a href="?a=start&amp;id=<?php echo $song['Pos']?>">
				<?=$song['Name']?>
			</a>
		</p>
	<?php } elseif($song['file'] != NULL) { ?>
		<p class="songLine">
			<a href="?a=remove&amp;id=<?php echo $song['Id']?>" title="Remove this song" class="removeid">x</a>
			<a href="?a=start&amp;id=<?php echo $song['Pos']?>">
				<?php echo $song['file']?>
			</a>
		</p>
	<?php } ?>
<?php } ?>
</div>
<div style="float: right;" class="bottombar">
	<span class="ajaxOutput">
		<span id="outVolup">Vol ++</span>
		<span id="outVoldown">Vol --</span>
		<span id="outNext">Next song</span>
		<span id="outPrev">Previous song</span>
		<span id="outPause">Paused</span>
		<span id="outPlay">Play</span>
	</span>
	Status: <?php if($status != 'stopped'): ?><a href="#current"><?php echo $status?></a><?php else: echo $status; endif;?> | Songs: <?php echo $mpd->playlist_count?> | Vol: <span id="currentvol"><?php echo $mpd->volume?></span>%
</div>
<div class="add">
	<form action="./" method="post">
		<input type="text" name="toadd" onclick="if(this.value=='Add dir or songs'){this.value='';}" onblur="if(this.value==''){this.value='Add dir or songs';}" value="Add dir or songs" /> <a href="?a=clearpl" title="Clear playlist"><img src="media/icons/table_row_delete.png" alt="Clear Playlist" /></a>
	</form>
</div>

