<?php
/**
 * Shared logic for the Review Fixes mass actions (approve / reject).
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\Controller\Result\Redirect;
use NavinDBhudiya\CatalogGuard\Model\PythonService;

abstract class AbstractMassAction extends Action
{
    public const ADMIN_RESOURCE = 'NavinDBhudiya_CatalogGuard::review';

    public function __construct(
        Context $context,
        protected readonly PythonService $service
    ) {
        parent::__construct($context);
    }

    /** Apply the action to one proposal id; returns true on success. */
    abstract protected function applyTo(string $id): bool;

    /** Past-tense verb for the success message ("approved" / "rejected"). */
    abstract protected function verb(): string;

    public function execute(): Redirect
    {
        $count = 0;
        foreach ($this->resolveIds() as $id) {
            if ($this->applyTo((string) $id)) {
                $count++;
            }
        }
        $this->messageManager->addSuccessMessage(
            __('%1 fix proposal(s) %2.', $count, $this->verb())
        );

        return $this->resultRedirectFactory->create()->setPath('catalogguard/review/index');
    }

    /**
     * Resolve the selected proposal ids, honoring "select all across pages".
     *
     * @return array<int, string>
     */
    private function resolveIds(): array
    {
        $selected = $this->getRequest()->getParam('selected');
        if (is_array($selected)) {
            return $selected;
        }

        $excluded = $this->getRequest()->getParam('excluded');
        if ($excluded === null) {
            return [];
        }

        // "Select all" — every pending proposal except the excluded ones.
        $excludedSet = is_array($excluded) ? array_flip($excluded) : [];
        $ids = [];
        foreach ($this->service->getPendingProposals(1, 100000)['items'] as $row) {
            $id = (string) ($row['id'] ?? '');
            if ($id !== '' && !isset($excludedSet[$id])) {
                $ids[] = $id;
            }
        }

        return $ids;
    }
}
