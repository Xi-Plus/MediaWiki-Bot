<?php
function WriteLog($message="") {
	global $C, $G;
	if (!isset($G["logcnt"])) {
		$G["logcnt"] = 0;
		$G["rdstr"] = substr(md5(uniqid(rand(),true)), 0, 4);
	}
	$G["logcnt"] ++;
	$time = date("Y-m-d H:i:s");
	$hash = md5(json_encode(array("time"=>$time, "message"=>$message)));
	$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}log` (`time`, `message`, `hash`) VALUES (:time, :message, :hash)");
	$sth->bindValue(":time", $time);
	$sth->bindValue(":message", "[".$G["rdstr"]."][".$G["logcnt"]."]".$message);
	$sth->bindValue(":hash", $hash);
	$sth->execute();
}
