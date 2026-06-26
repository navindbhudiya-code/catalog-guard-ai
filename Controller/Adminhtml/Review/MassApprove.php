<?php
/**
 * Mass-approve selected fix proposals (proxied to the Python service).
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

class MassApprove extends AbstractMassAction
{
    protected function applyTo(string $id): bool
    {
        return $this->service->approveProposal($id);
    }

    protected function verb(): string
    {
        return (string) __('approved');
    }
}
