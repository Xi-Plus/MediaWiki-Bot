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
require(__DIR__."/../function/log.php");

$timelimit = date("Y-m-d H:i:s", strtotime($_GET["limit"] ?? "-6 months"));
echo "顯示最後動作 < ".$timelimit." (".($_GET["limit"] ?? "-6 months").")<br>";

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lastedit` < :lastedit AND `lastlog` < :lastlog AND `lastusergetrights` < :lastusergetrights ORDER BY `lastedit` ASC, `lastlog` ASC");
$sth->bindValue(":lastedit", $timelimit);
$sth->bindValue(":lastlog", $timelimit);
$sth->bindValue(":lastusergetrights", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
echo "共有".count($row)."筆<br><br>";
$count = 1;

foreach ($row as $user) {
	$user["rights"] = explode("|", $user["rights"]);
	$user["rights"] = array_diff($user["rights"], $C["right-whitelist"]);
	if (count($user["rights"]) == 0) {
		continue;
	}
	?>
*{{User|<?=$user["name"]?>}}<br>
*:{{status2|新提案}}<br>
*:需複審或解除之權限：{{subst:int:group-<?php echo implode("}}、{{subst:int:group-", $user["rights"]); ?>}}<br>
*:理由：逾六個月沒有任何編輯活動、[[Special:用户贡献/<?=$user["name"]?>|<?php
if ($user["lastedit"] == "0000-00-00 00:00:00") {
	echo "從未編輯過";
} else {
	$time = strtotime($user["lastedit"]);
	echo "最後編輯在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
?>]]、[[Special:日志/<?=$user["name"]?>|<?php
if ($user["lastlog"] == "0000-00-00 00:00:00") {
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
