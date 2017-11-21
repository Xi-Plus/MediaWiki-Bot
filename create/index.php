<?php
$list = file_get_contents("input.txt");
$list = str_replace("\r", "", $list);
$list = explode("\n", $list);
$out = "";
foreach ($list as $page) {
	$res = file_get_contents("https://zh.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&rvlimit=1&rvdir=older&titles=".urlencode($page));
	$res = json_decode($res, true);
	$res = $res["query"]["pages"];
	$res = current($res);
	echo $res["revisions"][0]["timestamp"]." ".$page."\n";
	$out .= $res["revisions"][0]["timestamp"]."\t".$page."\n";
}
file_put_contents("out.csv", $out);
