<?php

/* Settings */
$mpdServer = 'localhost';
$mpdPort = '6600';
$mpdPassword = NULL;
$volDownSteps = 10;
$volUpSteps = 10;


/* Do not change */
ob_start();

include 'inc/mpd.class.php';
include 'inc/functions.php';

$mpd = new mpd($mpdServer, $mpdPort, $mpdPassword);

define('CURRENTARTIST', $mpd->playlist[$mpd->current_track_id]['Artist']);
define('CURRENTTRACK', $mpd->playlist[$mpd->current_track_id]['Title']);
define('CURRENTID', $mpd->playlist[$mpd->current_track_id]['Id']);

include 'tpl/header.tpl.php';

if($mpd->connected == FALSE) {
    	echo "Error: " .$mpd->errStr;
} else {
	$statusrow = explode("\n", $mpd->SendCommand('status'));
	
	foreach($statusrow as $row) {
		$get = explode(': ', $row);
		$status[$get[0]] = $get[1];
	}

	$times = explode(':', $status['time']);
	$CURRENTLENGTH = convertSecs($times[1]);
	$CURRENTTIME = convertSecs($times[0]);

	// fucking dirty
	if($mpd->state != 'stop') {
		$refresh = ((($times[1]-$times[0])*1000)+500);
		if($refresh < 1) { $refresh = 30500; }
		echo '<script type="text/javascript">setTimeout("location.reload(true);", ' . $refresh . ');</script>'."\n";
	}

	if(isset($_POST['toadd'])) {
		$object = $_POST['toadd'];

		$files = explode("\n", $mpd->SendCommand('lsinfo'));

		foreach($files as $row) {
			$file = explode(':', $row);
			$thefiles[][$file[0]] = ltrim($file[1]);
		}	

		foreach($thefiles as $search) {
			if(array_search($object, $search) == 'directory') {
				$dir = $mpd->GetDir($object);
				
				foreach($dir as $addRow) {
					$addArr[] = $addRow['file'];
				}
				
				$mpd->PLAddBulk($addArr);
				break;
			} else {
				$songs = explode(',', $object);

				$mpd->PLAddBulk($songs);
				break;
			}
		}
		$mpd->SendCommand('update');	
		header('Location: ./#current');
	}
	
	switch($_GET['a']) {
		case 'volup':
			$mpd->AdjustVolume($volUpSteps); break;
		case 'voldown':
			$mpd->AdjustVolume('-'.$volDownSteps); break;
		case 'play':
			$mpd->Play(); header('Location: ./#current'); break;
		case 'pause':
			$mpd->Pause(); header('Location: ./#current'); break;
		case 'prev':
			$mpd->Previous(); header('Location: ./#current'); break;
		case 'next':
			$mpd->Next(); header('Location: ./#current'); break;
		case 'stop':
			$mpd->Stop(); header('Location: ./#current'); break;
		case 'start':
			$songID = (int) $_GET['id']; 
			$mpd->SkipTo($songID); 
			header('Location: ./#current'); 
			break;
		case 'clearpl':
			$mpd->PLClear(); 
			header('Location: ./'); 
			break;
		case 'remove':
			$songID = (int) $_GET['id']; 
			$mpd->SendCommand('deleteid', $songID); 
			$mpd->RefreshInfo(); 
			header('Location: ./#current'); 
			break;
	}

	switch($mpd->state) {
		case 'play':
			$status = 'playing'; break;
		case 'pause':
			$status = 'paused'; break;
		default:
			$status = 'stopped'; break;
	}

	include 'tpl/main.tpl.php';
}

include 'tpl/footer.tpl.php';

?>

