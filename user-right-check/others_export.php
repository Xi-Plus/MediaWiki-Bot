<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0" />
</head>
<body>
<?php
require(__DIR__."/../config/config.php");
date_default_timezone_set('UTC');
@include(__DIR__."/config.php");
require(__DIR__."/function.php");
require(__DIR__."/../function/log.php");

$timelimit = date("Y-m-d H:i:s", strtotime($_GET["limit"] ?? $C["other_export_timelimit"]));
echo "顯示最後動作 < ".$timelimit." (".($_GET["limit"] ?? $C["other_export_timelimit"]).")<br>";

$noeditonly = "";
if (isset($_GET["noeditonly"])) {
	$noeditonly = " AND `lastedit` = '0000-00-00 00:00:00' ";
}
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lastedit` < :lastedit AND `lastlog` < :lastlog AND `lastusergetrights` < :lastusergetrights {$noeditonly} ORDER BY `lastedit` ASC, `lastlog` ASC");
$sth->bindValue(":lastedit", $timelimit);
$sth->bindValue(":lastlog", $timelimit);
$sth->bindValue(":lastusergetrights", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);

foreach ($row as $key => $user) {
	$row[$key]["rights"] = explode("|", $row[$key]["rights"]);
	if (in_array("bot", $row[$key]["rights"])) {
		$row[$key]["rights"] = array_diff($row[$key]["rights"], ["AWB"]);
	}
	$row[$key]["rights"] = array_diff($row[$key]["rights"], $C["right-whitelist"]);
	$row[$key]["rights"] = array_values($row[$key]["rights"]);
	if (count($row[$key]["rights"]) == 0) {
		unset($row[$key]);
		continue;
	}
	$row[$key]["time"] = 0;
	if ($row[$key]["lastedit"] !== $C['TIME_MIN']) {
		$row[$key]["time"] = max($row[$key]["time"], strtotime($row[$key]["lastedit"]));
	}
	if ($row[$key]["lastlog"] !== $C['TIME_MIN']) {
		$row[$key]["time"] = max($row[$key]["time"], strtotime($row[$key]["lastlog"]));
	}
	if ($row[$key]["lastusergetrights"] !== $C['TIME_MIN']) {
		$row[$key]["time"] = max($row[$key]["time"], strtotime($row[$key]["lastusergetrights"]));
	}
}
function cmp($a, $b) {
    if ($a["time"] == $b["time"]) {
        return 0;
    }
    return ($a["time"] < $b["time"]) ? -1 : 1;
}
usort($row, "cmp");

echo "共有".count($row)."筆<br><br>";

$month = 999;
foreach ($row as $user) {
	$nmonth = monthdiff($user["time"]);
	if ($month != $nmonth) {
		echo htmlspecialchars("<!-- ".$nmonth."個月 -->")."<br><br>";
		$month = $nmonth;
	}
	?>
*{{User|<?=$user["name"]?>}}<br>
*:{{status2|新提案}}<br>
*:需複審或解除之權限：<?php
foreach ($user["rights"] as $key => $value) {
	if ($key) {
		echo "、";
	}
	if ($value == $C["AWBright"]) {
		echo $C["AWBname"];
	} else {
		echo '{{subst:int:group-'.$value.'}}';
	}
}
?><br>
*:理由：逾六個月沒有任何編輯活動、[[Special:用户贡献/<?=$user["name"]?>|<?php
if ($user["lastedit"] == $C['TIME_MIN']) {
	echo "從未編輯過";
} else {
	$time = strtotime($user["lastedit"]);
	echo "最後編輯在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
?>]]、[[Special:日志/<?=$user["name"]?>|<?php
if ($user["lastlog"] == $C['TIME_MIN']) {
	echo "從未有日誌動作";
} else {
	$time = strtotime($user["lastlog"]);
	echo "最後日誌動作在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
?>]]、[[Special:用户权限/<?=$user["name"]?>|<?php
$time = strtotime($user["lastusergetrights"]);
echo "最後授權在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
?>]]<br>
*:~~~~<br><br>
<?php
}
?>
</body>
</html>
