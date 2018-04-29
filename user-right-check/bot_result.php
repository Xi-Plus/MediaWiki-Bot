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

$timelimit = date("Y-m-d H:i:s", strtotime($C["bot_result_timelimit"]));
echo "顯示最後動作 < ".$timelimit."<br>";

if (isset($_POST["owner"])) {
	$time = strtotime($_POST["time"]);
	if ($time === false) {
		echo "更新".$_POST["owner"]."的最後編輯時間失敗<br>";
	} else {
		$time = date("Y-m-d H:i:s", $time);
		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `userlastedit` = :userlastedit WHERE `botname` = :botname");
		$sth->bindValue(":userlastedit", $time);
		$sth->bindValue(":botname", $_POST["botname"]);
		$sth->execute();
		WriteLog("update user ".$_POST["owner"]." lastedit = ".$time);
		echo "成功更新".$_POST["owner"]."的最後編輯時間為".$time."<br>";
	}
}

if (isset($_POST["reported"])) {
	$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `reported` = 1 WHERE `botname` = :botname");
	$sth->bindValue(":botname", $_POST["bot"]);
	$sth->execute();
	WriteLog("update user ".$_POST["bot"]." reported");
	echo "成功將".$_POST["bot"]."標記為已報告<br>";
}


$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `botlastedit` < :botlastedit AND `botlastlog` < :botlastlog AND `reported` = 0 AND `userid` > 0 ORDER BY `botlastedit` ASC, `botlastlog` ASC");
$sth->bindValue(":botlastedit", $timelimit);
$sth->bindValue(":botlastlog", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
echo "共有".count($row)."筆<br>";
$count = 1;
?>
<table>
<tr>
	<th>#</th>
	<th>bot</th>
	<th>bot last edit</th>
	<th>bot last log</th>
	<th>bot rights</th>
	<th>owner</th>
	<th>reported</th>
</tr>
<?php
foreach ($row as $bot) {
	?><tr>
		<td><?php echo ($count++); ?></td>
		<td><a href="https://zh.wikipedia.org/wiki/User:<?=$bot["botname"]?>" target="_blank"><?=$bot["botname"]?></a></td>
		<td>
			<form method="post" style="margin: 0px;">
				<a href="https://zh.wikipedia.org/wiki/Special:用户贡献/<?=$bot["botname"]?>" target="_blank"><?=$bot["botlastedit"]?></a>
				<input type="text" name="time">
				<input type="hidden" name="botname" value="<?=$bot["botname"]?>">
			</form>
		</td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:日志/<?=$bot["botname"]?>" target="_blank"><?=$bot["botlastlog"]?></a></td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:用户权限/<?=$bot["botname"]?>" target="_blank"><?=$bot["botrights"]?></a></td>
		<td><a href="https://zh.wikipedia.org/wiki/User:<?=$bot["username"]?>" target="_blank"><?=$bot["username"]?></a></td>
		<td>
			<form method="post" style="margin: 0px;">
				<input type="hidden" name="bot" value="<?=$bot["botname"]?>">
				<input type="submit" value="reported" name="reported">
			</form>
		</td>
	</tr><?php
}
?>
</table>
</body>
</html>
