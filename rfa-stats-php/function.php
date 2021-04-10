<?php

function voting_info($support, $oppose) {
	if ($support < 25) {
		if ($oppose <= 5) {
			return "要獲選還需" . (25 - $support) . "張支持票，同時能有至多" . (5 - $oppose) . "張反對票";
		} else {
			return "要獲選還需" . ($oppose * 4 - $support) . "張支持票";
		}
	} else {
		if ($support >= $oppose * 4) {
			return "要獲選最多還能有" . (floor($support / 4) - $oppose) . "張反對票";
		} else {
			return "要獲選還需" . ($oppose * 4 - $support) . "張支持票";
		}
	}
}
