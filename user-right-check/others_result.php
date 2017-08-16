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

$timelimit = date("Y-m-d H:i:s", strtotime($_GET["limit"] ?? $C["other_result_timelimit"]));
echo "顯示最後動作 < ".$timelimit." (".($_GET["limit"] ?? $C["other_result_timelimit"]).")<br>";

if (isset($_POST["name"])) {
	$time = false;
	if (isset($_POST["lastedit"])) {
		$posttime = $_POST["lastedit"];
		if (preg_match("/(\d+)年(\d+)月(\d+)日 (?:.+?) (\d+):(\d+)/", $posttime, $m)) {
			$time = date("Y-m-d H:i:s", strtotime("{$m[1]}/{$m[2]}/{$m[3]} {$m[4]}:{$m[5]}")-60*60*8);
		} else if (strtotime($posttime)) {
			$time = date("Y-m-d H:i:s", strtotime($posttime)-60*60*8);
		} else {
			echo "更新".$_POST["name"]."的".$colname."失敗<br>";
		}
		if ($time !== false) {
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `lastedit` = :lastedit, `lasttime` = :lasttime WHERE `name` = :name");
			$sth->bindValue(":lastedit", $time);
			$sth->bindValue(":lasttime", $time);
			$sth->bindValue(":name", $_POST["name"]);
			$sth->execute();
			WriteLog("update user ".$_POST["name"]." lastedit = ".$time);
			echo "成功更新".$_POST["name"]."的lastedit為".$time."<br>";
		}
	} else if (isset($_POST["noticed"])) {
		$time = date("Y-m-d H:i:s");
		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `noticetime` = :noticetime WHERE `name` = :name");
		$sth->bindValue(":noticetime", $time);
		$sth->bindValue(":name", $_POST["name"]);
		$sth->execute();
		WriteLog("update user ".$_POST["name"]." noticetime = ".$time);
		echo "成功更新".$_POST["name"]."的noticetime為".$time."<br>";
		$time = date("Y-m-d H:i:s");
	}
}

$noeditonly = "";
if (isset($_GET["noeditonly"])) {
	$noeditonly = " AND `lastedit` = '0000-00-00 00:00:00' ";
}
if (!isset($_GET["ignorenotice"])) {
	$noeditonly = " AND `noticetime` < '".date("Y-m-d H:i:s", time()-86400*7)."' ";
}
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime {$noeditonly} ORDER BY `lasttime` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);

foreach ($row as $key => $user) {
	if (isset($_GET["fullright"])) {
		$row[$key]["fullrights"] = $row[$key]["rights"];
	}
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
	if (isset($_GET["fullright"])) {
		$row[$key]["rights"] = $row[$key]["fullrights"];
	} else {
		$row[$key]["rights"] = implode("|", $row[$key]["rights"]);
	}
}
$row = array_values($row);

echo "共有".count($row)."筆<br>";

$count = 1;
?>
<table>
<tr>
	<th>#</th>
	<th>user</th>
	<th>last edit</th>
	<th>last log</th>
	<th>last usergetrights</th>
	<th>last time</th>
	<th>notfice time</th>
	<th>rights</th>
</tr>
<?php
foreach ($row as $key => $user) {
	?><tr <?php
		if ($key % 10 >= 5) {
			echo 'style="background: #ddd;"';
		}
	?>>
		<td><?php echo ($count++); ?></td>
		<td><a href="https://zh.wikipedia.org/wiki/User:<?=$user["name"]?>" target="_blank"><?=$user["name"]?></a> (<a href="https://zh.wikipedia.org/wiki/User_talk:<?=$user["name"]?>" target="_blank">Talk</a>)</td>
		<td>
			<form method="post" style="margin: 0px;">
				<a href="https://zh.wikipedia.org/wiki/Special:用户贡献/<?=$user["name"]?>" target="_blank"><?=$user["lastedit"]?></a>
				<input type="text" name="lastedit" required>
				<input type="hidden" name="name" value="<?=$user["name"]?>">
			</form>
		</td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:日志/<?=$user["name"]?>" target="_blank"><?=$user["lastlog"]?></a></td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:日志/rights?page=User:<?=$user["name"]?>" target="_blank"><?=$user["lastusergetrights"]?></a></td>
		<td><?=$user["lasttime"]?></td>
		<td>
			<form method="post" style="margin: 0px; white-space: nowrap;">
				<?=$user["noticetime"]?>
				<input type="hidden" name="name" value="<?=$user["name"]?>">
				<input type="submit" value="noticed" name="noticed">
			</form>
		</td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:用户权限/<?=$user["name"]?>" target="_blank"><?=$user["rights"]?></a></td>
	</tr><?php
}
?>
</table>
</body>
</html>
