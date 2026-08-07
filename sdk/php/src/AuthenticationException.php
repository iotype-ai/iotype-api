<?php

declare(strict_types=1);

namespace Iotype;

/**
 * HTTP 401.
 *
 * The docs list four causes for this one status: missing header, malformed
 * token, expired token, **or exhausted token balance**. Mention the balance
 * case when surfacing this to a user.
 */
class AuthenticationException extends IotypeException
{
}
