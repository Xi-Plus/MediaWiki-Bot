<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";

$C["User-Agent"] = "User:A2093064-bot blocked-ip";

$C["DBTBprefix"] = "BlockedIP";

$C["cookiefile"] = __DIR__ . "/../tmp/blocked-ip-cookie.txt";

$G["db"] = new PDO('mysql:host=' . $C["DBhost"] . ';dbname=' . $C["DBname"] . ';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
