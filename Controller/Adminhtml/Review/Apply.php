<?php
/**
 * "Apply Approved" — writes APPROVED fixes to the store via the Python service.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\Controller\Result\Json;
use Magento\Framework\Controller\Result\JsonFactory;
use NavinDBhudiya\CatalogGuard\Model\PythonService;
use Psr\Log\LoggerInterface;

class Apply extends Action
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
            $outcome = $this->service->applyApproved();
            if (!$outcome['success']) {
                return $result->setData([
                    'success' => false,
                    'message' => $outcome['message'] ?: 'Apply failed.',
                ]);
            }

            return $result->setData([
                'success' => true,
                'message' => (string) __(
                    '%1 approved fix(es) applied to the store (batch %2).',
                    $outcome['applied'],
                    $outcome['batch']
                ),
            ]);
        } catch (\Throwable $e) {
            $this->logger->error('CatalogGuard apply failed: ' . $e->getMessage());

            return $result->setData(['success' => false, 'message' => $e->getMessage()]);
        }
    }
}
