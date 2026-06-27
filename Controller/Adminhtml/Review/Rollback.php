<?php
/**
 * "Rollback Last Batch" — reverts the most recent applied batch.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\Controller\Result\Json;
use Magento\Framework\Controller\Result\JsonFactory;
use NavinDBhudiya\CatalogGuard\Model\PythonService;
use Psr\Log\LoggerInterface;

class Rollback extends Action
{
    public const ADMIN_RESOURCE = 'NavinDBhudiya_CatalogGuard::review';

    public function __construct(
        Context $context,
        private readonly JsonFactory $resultJsonFactory,
        private readonly PythonService $service,
        private readonly LoggerInterface $logger
    ) {
        parent::__construct($context);
    }

    public function execute(): Json
    {
        $result = $this->resultJsonFactory->create();

        try {
            $outcome = $this->service->rollbackLast();
            if (!$outcome['success']) {
                return $result->setData([
                    'success' => false,
                    'message' => $outcome['message'] ?: 'Rollback failed.',
                ]);
            }

            return $result->setData([
                'success' => true,
                'message' => (string) __('%1 change(s) rolled back.', $outcome['reverted']),
            ]);
        } catch (\Throwable $e) {
            $this->logger->error('CatalogGuard rollback failed: ' . $e->getMessage());

            return $result->setData(['success' => false, 'message' => $e->getMessage()]);
        }
    }
}
