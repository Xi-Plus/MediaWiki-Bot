<?php
require("config.php");

$list = file_get_contents("input.txt");
$list = str_replace("\r", "", $list);
$list = explode("\n", $list);
$output = "";
foreach ($list as $page) {
	$res = file_get_contents(sprintf($C["url"], urlencode($page)));
	$res = json_decode($res, true);
	$text = $res["result"] . " " . $page . "\n";
	echo $text;
	$output .= $text;
}
file_put_contents("output.txt", $output);
