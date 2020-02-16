<?php
function WriteLog($message = "")
{
    global $C, $G;
    if (!isset($G["logcnt"])) {
        $G["logcnt"] = 0;
        $G["rdstr"] = substr(md5(uniqid(rand(), true)), 0, 4);
    }
    $G["logcnt"]++;
    $time = date("Y-m-d H:i:s");
    $sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}log` (`time`, `message`) VALUES (:time, :message)");
    $sth->bindValue(":time", $time);
    $sth->bindValue(":message", "[" . $G["rdstr"] . "][" . $G["logcnt"] . "]" . $message);
    $sth->execute();
}

function ClearLog()
{
    global $C, $G;
    $sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}log` WHERE `time` < :time");
    $sth->bindValue(":time", date("Y-m-d H:i:s", strtotime("-1 month")));
    $sth->execute();
}
