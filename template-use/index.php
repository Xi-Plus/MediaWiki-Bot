<?php
$list = file_get_contents("input.txt");
$list = str_replace("\r", "", $list);
$list = explode("\n", $list);
foreach ($list as $page) {
	$res = file_get_contents("https://xiplus.twbbs.org/Xiplus-zhWP/Template-transclusion-count.php?namespace=10&title=" . urlencode($page));
	$res = json_decode($res, true);
	echo $res["result"] . " " . $page . "\n";
}
