<?php

function convertSecs($secs) {
	if ($secs<0) 
		return false;
	
	$m = (int) ($secs / 60); 
	$s = $secs % 60;
	
	$h = (int) ($m / 60); 
	$m = $m % 60;
	
	return array($h, $m, $s);
}

?>
