<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
@include(__DIR__."/function.php");

$time = date("Y-m-d H:i:s");

if (isset($argv[1])) {
	$C["fetchuser"] = $argv[1];
}
echo "fetch ".$C["fetchuser"]."\n";
$text = file_get_contents(__DIR__."/list/".$C["fetchuser"].".csv");
if ($text === false) {
	exit("user not found\n");
}
$text = explode("\n", $text);

$result = [];
$vote = [];
$code = [];
foreach ($text as $row) {
	$row = str_getcsv($row);
	if (!isset($row[3])) {
		continue;
	}
	$v = $row[2];
	$c = $row[3];
	$v = votetocode($v);
	$c = closetocode($c);
	if ($v == "" || $c == "") {
		continue;
	}
	@$result[$v][$c]++;
	@$vote[$v] = true;
	@$code[$c] = true;
}
function cmpvote($a, $b) {
	if ($b == "nominator") {
		return 1;
	} else if ($b == "fwdcsd") {
		if ($a == "nominator") {
			return -1;
		}
		return 1;
	} else if ($a == "nominator" || $a == "fwdcsd") {
		return -1;
	}
    return ($a < $b) ? -1 : 1;
}
uksort($vote, "cmpvote");
function cmpcode($a, $b) {
	if ($a == "ir") {
		return 1;
	} else if ($b == "ir") {
		return -1;
	}
    return ($a < $b) ? -1 : 1;
}
uksort($code, "cmpcode");

$output = file_get_contents("template.html");
$output = str_replace("<!--title-->", $C["fetchuser"], $output);

$out = "";
foreach ($result as $key1 => $counts) {
	$out .= "alldata['".$key1."'] = [['提刪', '數量']";
	foreach ($counts as $key2 => $count) {
		$out .= ",";
		$out .= "[";
		$out .= '"'.$key2.'",';
		$out .= $count;
		$out .= "]";
	}
	$out .= "];\n";
}
$output = str_replace("/*data1*/", $out, $output);

$out = "<tr>\n<td>投票 \ 結果</td>\n";
foreach ($code as $c => $_) {
	$out .= "<td>".$c."</td>\n";
}
$out .= "<td>show chart</td>";
$out .= "</tr>\n";
foreach ($vote as $v => $_) {
	$out .= "<tr>";
	$out .= "<td>".$v."</td>\n";
	foreach ($code as $c => $_) {
		$out .= "<td ".($c==$v?"style='background-color: #9f9;'":"").">".($result[$v][$c]??0)."</td>\n";
	}
	$out .= "<td><button onclick='vote=\"".$v."\";drawChart();'>show chart</button></td>\n";
	$out .= "</tr>\n";
}
$output = str_replace("<!--data2-->", $out, $output);

$out = "<tr>\n<td>頁面</td><td>時間</td><td>投票</td><td>結果</td>\n";
foreach ($text as $row) {
	$row = str_getcsv($row);
	if (!isset($row[3])) {
		continue;
	}
	$v = $row[2];
	$c = $row[3];
	$v = votetocode($v);
	$c = closetocode($c);
	if ($v == "" || $c == "") {
		continue;
	}
	$out .= "<tr>";
	$title = $row[1];
	if (mb_strlen($title) > 20) {
		$title = mb_substr($title, 0, 20)."...";
	}
	$out .= "<td><a href='https://zh.wikipedia.org/wiki/".$row[0]."#".$row[1]."' target='_blank'>".$title."</a></td>\n";
	$out .= "<td>".str_replace("Wikipedia:頁面存廢討論/記錄/", "", $row[0])."</td>\n";
	$out .= "<td>".$v."</td>\n";
	$out .= "<td>".$c."</td>\n";
	$out .= "</tr>\n";
}
$output = str_replace("<!--data3-->", $out, $output);

$output = str_replace("<!--time-->", $time, $output);
file_put_contents(__DIR__."/list/".$C["fetchuser"].".html", $output);

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
