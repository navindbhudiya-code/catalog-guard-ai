<?php
/**
 * Mass-reject selected fix proposals (proxied to the Python service).
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

class MassReject extends AbstractMassAction
{
    protected function applyTo(string $id): bool
    {
        return $this->service->rejectProposal($id);
    }

    protected function verb(): string
    {
        return (string) __('rejected');
    }
}
