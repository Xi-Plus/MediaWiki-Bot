<?php

function votetocode($vote) {
	global $C;
	$vote = strtolower($vote);
	foreach ($C["votetemplate"] as $key => $values) {
		foreach ($values as $value) {
			if ($vote == strtolower($value)) {
				return $key;
			}
		}
	}
	return "";
}

function closetocode($code) {
	global $C;
	foreach ($C["closecode"] as $key => $value) {
		if (in_array($code, $value)) {
			return $key;
		}
	}
	if (preg_match("(理由消失|撤回|解決)", $code)) {
		return "k";
	}
	if (preg_match("(侵权|侵權|刪除)", $code)) {
		return "d";
	}
	return "";
}
