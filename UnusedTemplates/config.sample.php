<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["templatecount"] = "https://example.com/Template-transclusion-count.php?namespace=10&title=";
$C["user"] = "";
$C["pass"] = "";

$C["User-Agent"] = "User:A2093064-bot UnusedTemplates";

$C["DBTBprefix"] = "UnusedTemplates_";

$C["cookiefile"] = __DIR__ . "/../tmp/UnusedTemplates-cookie.txt";

$C["fail_retry"] = 5;

$G["db"] = new PDO('mysql:host=' . $C["DBhost"] . ';dbname=' . $C["DBname"] . ';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
